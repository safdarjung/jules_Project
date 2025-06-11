import pytest
from typing import List, Dict, Any
from unittest.mock import Mock # Changed from MagicMock to Mock for simplicity if not needing magic methods

from ai_sdr_assistant.lead_ingestion import WebsiteFormIngestor, LeadIngestorBase
from ai_sdr_assistant.lead_prospecting.prospector import ProspectorBase, SimpleWebSearchProspector
from ai_sdr_assistant.config.settings import USER_PROFILE # For providing to ingestor if needed

# --- Mocks and Fixtures ---

class MockProspector(ProspectorBase):
    """A mock prospector for testing purposes."""
    def __init__(self, predefined_companies: List[Dict[str, str]]):
        self.predefined_companies = predefined_companies
        self.find_companies_called_with_profile: Optional[Dict[str, Any]] = None

    def find_companies(self, user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        self.find_companies_called_with_profile = user_profile
        print(f"MockProspector.find_companies called with user_profile containing my_company_name: {user_profile.get('my_company_name')}")
        return self.predefined_companies

@pytest.fixture
def sample_companies_from_prospector() -> List[Dict[str, str]]:
    return [
        {'company_name': 'Test Alpha Corp', 'website': 'alpha.example.test', 'source': 'mock_prospector', 'industry_hint': 'Tech'},
        {'company_name': 'Test Beta Solutions', 'website': 'beta.example.test', 'source': 'mock_prospector', 'location_hint': 'Remote'},
        {'company_name': 'Gamma Services', 'website': 'gamma.example.test', 'source': 'mock_prospector_gamma'} # No specific hint
    ]

@pytest.fixture
def mock_prospector_instance(sample_companies_from_prospector: List[Dict[str, str]]) -> MockProspector:
    return MockProspector(predefined_companies=sample_companies_from_prospector)

# --- Tests for WebsiteFormIngestor ---

def test_website_form_ingestor_default_init():
    """Test WebsiteFormIngestor __init__ with default SimpleWebSearchProspector."""
    ingestor = WebsiteFormIngestor()
    assert isinstance(ingestor, LeadIngestorBase)
    assert isinstance(ingestor.prospector, SimpleWebSearchProspector)
    assert ingestor.user_profile == USER_PROFILE # Check if it loads the actual USER_PROFILE

def test_website_form_ingestor_custom_init(mock_prospector_instance: MockProspector):
    """Test WebsiteFormIngestor __init__ with a custom prospector."""
    ingestor = WebsiteFormIngestor(prospector=mock_prospector_instance)
    assert isinstance(ingestor, LeadIngestorBase)
    assert ingestor.prospector == mock_prospector_instance
    assert ingestor.user_profile == USER_PROFILE

def test_website_form_ingestor_ingest_transforms_prospects(
    mock_prospector_instance: MockProspector,
    sample_companies_from_prospector: List[Dict[str, str]]
):
    """Test ingest() method transforms companies from prospector into leads."""
    ingestor = WebsiteFormIngestor(prospector=mock_prospector_instance)
    ingested_leads = ingestor.ingest()

    assert mock_prospector_instance.find_companies_called_with_profile is not None, "Prospector's find_companies was not called"
    # Check if the USER_PROFILE from settings was passed to the prospector
    assert mock_prospector_instance.find_companies_called_with_profile.get('my_company_name') == USER_PROFILE.get('my_company_name')


    assert len(ingested_leads) == len(sample_companies_from_prospector)

    for i, lead in enumerate(ingested_leads):
        original_company = sample_companies_from_prospector[i]

        # Check transformation
        expected_email = f"info@{original_company['website']}"
        expected_name = f"Contact at {original_company['company_name']}"

        assert lead['email'] == expected_email
        assert lead['name'] == expected_name
        assert lead['company_name'] == original_company['company_name']
        assert lead['website'] == original_company['website']
        assert lead['source'] == original_company['source'] # Ensure other fields are carried over

        # Check for hints if they were in the original company data
        if 'industry_hint' in original_company:
            assert lead['industry_hint'] == original_company['industry_hint']
        if 'location_hint' in original_company:
            assert lead['location_hint'] == original_company['location_hint']

def test_website_form_ingestor_ingest_empty_prospects(mock_prospector_instance: MockProspector):
    """Test ingest() when the prospector returns no companies."""
    mock_prospector_instance.predefined_companies = [] # Configure mock to return empty list
    ingestor = WebsiteFormIngestor(prospector=mock_prospector_instance)
    ingested_leads = ingestor.ingest()

    assert len(ingested_leads) == 0
    assert mock_prospector_instance.find_companies_called_with_profile is not None


# Keep old tests if they test different aspects, or remove if redundant.
# The original tests for WebsiteFormIngestor were for hardcoded leads.
# This new functionality replaces that, so those specific tests are no longer valid.
# I'm removing the very first original test for WebsiteFormIngestor as it's covered/obsoleted.

# Original test_website_form_ingestor_ingest (now obsolete due to changes):
# def test_website_form_ingestor_ingest():
#     """Test the ingest() method of WebsiteFormIngestor."""
#     ingestor = WebsiteFormIngestor() # This will now use SimpleWebSearchProspector
#     leads: List[Dict[str, str]] = ingestor.ingest() # Will return leads from SimpleWebSearchProspector
#
#     assert isinstance(leads, list)
#     # The number of leads depends on SimpleWebSearchProspector's output
#     # assert len(leads) > 0
#
#     for lead in leads:
#         assert isinstance(lead, dict)
#         assert 'email' in lead
#         assert isinstance(lead['email'], str)
#         assert '@' in lead['email']
#         assert 'name' in lead
#         assert isinstance(lead['name'], str)
#         assert 'company_name' in lead # Added by new transformation
#         assert 'website' in lead # Added by new transformation

if __name__ == '__main__':
    pytest.main()
