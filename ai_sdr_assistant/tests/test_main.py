import pytest
from unittest.mock import patch, MagicMock, call # Added call
from typing import Dict, List, Any

# Module to be tested
from ai_sdr_assistant.main import run_sdr_workflow

# Mocks for dependencies
from ai_sdr_assistant.lead_prospecting.prospector import ProspectorBase
from ai_sdr_assistant.crm import CRMHandlerBase # For type hinting mock_crm_handler

# It's good practice to use the actual USER_PROFILE and IDEAL_CUSTOMER_PROFILE
# from settings to make the integration test more realistic, unless they cause side effects.
# from ai_sdr_assistant.config.settings import USER_PROFILE, IDEAL_CUSTOMER_PROFILE

# --- Mock Classes ---

class MockTestProspector(ProspectorBase):
    def __init__(self, companies_to_return: List[Dict[str, str]]):
        self.companies = companies_to_return
        self.find_companies_call_count = 0
        self.user_profile_passed: Optional[Dict[str, Any]] = None

    def find_companies(self, user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        self.find_companies_call_count += 1
        self.user_profile_passed = user_profile
        # Simulate prospector output, including hints that enricher and qualifier might use
        return self.companies

# Mock CRM Handler can be used to check interactions
# We can use MagicMock for this to simplify tracking calls if MockCRMHandler itself isn't easy to inspect
# Or, we can enhance MockCRMHandler for easier inspection in tests. For now, MagicMock is fine.

# --- Fixtures ---

@pytest.fixture
def mock_prospects() -> List[Dict[str, str]]:
    return [
        {
            'company_name': 'Qualified Tech Co',
            'website': 'qualifiedtech.example.com',
            'source': 'test_prospector',
            'industry_hint': 'Software', # Matches default ICP
            # 'size_hint' could be added if SimpleCompanyInfoEnricher uses it to create 'size'
        },
        {
            'company_name': 'Unqualified Retail Inc',
            'website': 'unqualifiedretail.example.com',
            'source': 'test_prospector',
            'industry_hint': 'Retail', # Does not match default ICP
        },
        {
            'company_name': 'No Info Corp',
            'website': 'noinfo.example.com',
            'source': 'test_prospector'
            # No hints, will rely on enricher's defaults or lack thereof
        }
    ]

# --- Patching Services for Workflow Test ---

@patch('ai_sdr_assistant.main.SimpleWebSearchProspector') # Target where it's IMPORTED and USED
@patch('ai_sdr_assistant.main.MockCRMHandler')
@patch('ai_sdr_assistant.main.SimpleCompanyInfoEnricher')
@patch('ai_sdr_assistant.main.ICPQualifier')
@patch('ai_sdr_assistant.main.EmailDraftAction')
@patch('ai_sdr_assistant.main.TagLeadInCRMAction')
def test_run_sdr_workflow_integration(
    MockTagAction, MockEmailAction, MockQualifier,
    MockEnricher, MockCRM, MockProspectorClass, # Order matches @patch decorators (bottom-up)
    mock_prospects: List[Dict[str, str]]
):
    # --- Configure Mocks ---

    # Prospector mock (instance of our MockTestProspector)
    mock_prospector_instance = MockTestProspector(companies_to_return=mock_prospects)
    MockProspectorClass.return_value = mock_prospector_instance # When SimpleWebSearchProspector() is called

    # CRM mock
    mock_crm_instance = MockCRM.return_value
    # Simulate get_lead not finding leads initially for the pre-population step
    mock_crm_instance.get_lead.return_value = None
    # mock_crm_instance.create_lead = MagicMock() # Already a MagicMock by default
    # mock_crm_instance.update_lead_status = MagicMock()
    # mock_crm_instance.add_note_to_lead = MagicMock()

    # Enricher mock
    mock_enricher_instance = MockEnricher.return_value
    def enrich_side_effect(lead: Dict[str, Any]) -> Dict[str, Any]:
        # Simple pass-through or add a known field for testing
        enriched = lead.copy()
        enriched['enriched_by_mock'] = True
        if enriched.get('company_name') == 'Qualified Tech Co':
            enriched['industry'] = 'Software' # Ensure it gets this for qualification
            enriched['size'] = '50-200 employees' # Ensure it gets this
        elif enriched.get('company_name') == 'Unqualified Retail Inc':
            enriched['industry'] = 'Retail'
            enriched['size'] = '10-20 employees'
        # For 'No Info Corp', let it be sparse
        return enriched
    mock_enricher_instance.enrich.side_effect = enrich_side_effect

    # Qualifier mock
    mock_qualifier_instance = MockQualifier.return_value
    def qualify_side_effect(lead: Dict[str, Any]) -> Dict[str, Any]:
        if lead.get('company_name') == 'Qualified Tech Co' and lead.get('industry') == 'Software':
            return {'qualified': True, 'summary': 'Mock Qualified'}
        return {'qualified': False, 'summary': 'Mock Unqualified'}
    mock_qualifier_instance.qualify.side_effect = qualify_side_effect

    # Action mocks
    mock_email_action_instance = MockEmailAction.return_value
    # mock_email_action_instance.execute.return_value = {'action_type': 'mock_email_drafted', 'status_message': 'Mock email sent'}

    mock_tag_action_instance = MockTagAction.return_value
    # mock_tag_action_instance.execute.return_value = {'action_type': 'mock_crm_tagged', 'status_message': 'Mock lead tagged'}

    # --- Run the workflow ---
    run_sdr_workflow()

    # --- Assertions ---

    # 1. Prospector usage
    # The prospector is called twice: once for pre-populating CRM, once by ingestor.
    assert mock_prospector_instance.find_companies_call_count == 2
    assert mock_prospector_instance.user_profile_passed is not None # Check USER_PROFILE was passed

    # 2. CRM interactions
    # Check pre-population calls to create_lead for each prospect
    expected_crm_create_calls = []
    for prospect in mock_prospects:
        # Estimate the email that main.py would generate for CRM pre-population
        email = f"contact@{prospect.get('website','').replace('www.','')}" if prospect.get('website') else f"contact@{prospect.get('company_name','unknown').lower().replace(' ','')}.example.com"
        expected_crm_create_calls.append(call({'company_name': prospect['company_name'], 'website': prospect['website'], 'email': email, 'status': 'prospected', 'source': prospect['source']}))
    mock_crm_instance.create_lead.assert_has_calls(expected_crm_create_calls, any_order=False) # Order matters here for the pre-population loop

    # 3. Enrichment and Qualification
    assert mock_enricher_instance.enrich.call_count == len(mock_prospects)
    assert mock_qualifier_instance.qualify.call_count == len(mock_prospects)

    # 4. Action dispatch
    # One lead ('Qualified Tech Co') should be qualified, two unqualified.
    assert mock_email_action_instance.execute.call_count == 1
    assert mock_tag_action_instance.execute.call_count == 2

    # Check that EmailDraftAction was called with the qualified lead
    # The actual lead data passed to execute would be after ingestor transformation and mock enrichment
    qualified_lead_arg = mock_email_action_instance.execute.call_args_list[0][0][0] # First arg of first call
    assert qualified_lead_arg['company_name'] == 'Qualified Tech Co'
    assert qualified_lead_arg['enriched_by_mock'] is True # From mock enricher

    # Check that TagLeadInCRMAction was called for the two unqualified leads
    unqualified_lead_args = [args[0][0] for args in mock_tag_action_instance.execute.call_args_list]
    assert any(arg['company_name'] == 'Unqualified Retail Inc' for arg in unqualified_lead_args)
    assert any(arg['company_name'] == 'No Info Corp' for arg in unqualified_lead_args)


if __name__ == '__main__':
    pytest.main(["-v", __file__]) # Run with verbose output for this test file
