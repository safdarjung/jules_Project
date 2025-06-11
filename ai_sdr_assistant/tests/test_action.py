import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

from ai_sdr_assistant.action import EmailDraftAction, TagLeadInCRMAction, ActionHandlerBase
from ai_sdr_assistant.crm import MockCRMHandler, CRMHandlerBase

# --- Fixtures ---

@pytest.fixture
def sample_qualified_lead() -> Dict[str, Any]:
    return {
        'email': 'ceo@example.com',
        'name': 'Jane Doe',
        'company_name': 'Example Corp',
        'industry': 'Software',
        'size': '100-250 employees',
        'domain': 'example.com',
        'enrichment_notes': 'Highly promising lead.'
    }

@pytest.fixture
def sample_unqualified_lead() -> Dict[str, Any]:
    return {
        'email': 'contact@smallbiz.com',
        'name': 'John Smith',
        'company_name': 'Small Biz Ltd',
        'industry': 'Retail',
        'size': '1-10 employees',
        'domain': 'smallbiz.com'
    }

@pytest.fixture
def sample_qualification_result_qualified() -> Dict[str, Any]:
    return {
        'qualified': True,
        'reasons': {'industry_match': True, 'size_match': True},
        'summary': 'Matches industry and size criteria.',
        'icp_criteria_used': {'industry': 'Software', 'min_employees': 50}
    }

@pytest.fixture
def sample_qualification_result_unqualified() -> Dict[str, Any]:
    return {
        'qualified': False,
        'reasons': {'industry_match': False, 'size_match': True},
        'summary': "Industry 'Retail' does not match required 'Software'.",
        'icp_criteria_used': {'industry': 'Software', 'min_employees': 50}
    }

@pytest.fixture
def email_action() -> EmailDraftAction:
    return EmailDraftAction(
        sdr_name="Test SDR",
        your_company_name="Test Solutions Inc.",
        product_service_name="our amazing test product"
    )

@pytest.fixture
def mock_crm_handler() -> MockCRMHandler:
    # Using a real MockCRMHandler instance
    handler = MockCRMHandler()
    # We can spy on its methods if needed, or check its internal state for some tests.
    # For more complex scenarios, unittest.mock.MagicMock could be used for the handler itself.
    return handler


@pytest.fixture
def tag_action(mock_crm_handler: MockCRMHandler) -> TagLeadInCRMAction:
    return TagLeadInCRMAction(crm_handler=mock_crm_handler)

# --- Tests for EmailDraftAction ---

def test_email_draft_action_instance(email_action: EmailDraftAction):
    """Test EmailDraftAction instantiation."""
    assert isinstance(email_action, ActionHandlerBase)
    assert email_action.sdr_name == "Test SDR"

def test_email_draft_action_execute(email_action: EmailDraftAction, sample_qualified_lead: Dict[str, Any], sample_qualification_result_qualified: Dict[str, Any]):
    """Test EmailDraftAction's execute method for a qualified lead."""
    result = email_action.execute(sample_qualified_lead, sample_qualification_result_qualified)

    assert result['action_type'] == 'email_drafted'
    assert result['lead_email'] == sample_qualified_lead['email']
    assert isinstance(result['email_subject'], str)
    assert isinstance(result['email_body'], str)
    assert result['assigned_to_sdr'] == "human_sdr_placeholder@example.com" # Default from class

    # Check content for placeholders
    assert sample_qualified_lead['company_name'] in result['email_subject']
    assert sample_qualified_lead['name'] in result['email_body']
    assert sample_qualified_lead['company_name'] in result['email_body']
    assert sample_qualified_lead['industry'] in result['email_body']
    assert sample_qualified_lead['size'] in result['email_body']
    assert email_action.product_service_name in result['email_body']
    assert email_action.sdr_name in result['email_body']
    assert email_action.your_company_name in result['email_body']
    assert "Email drafted for ceo@example.com to Example Corp." in result['status_message']

def test_email_draft_action_execute_missing_fields(email_action: EmailDraftAction):
    """Test EmailDraftAction with missing fields in the lead."""
    lead_missing_fields = {'email': 'test@example.com'} # Missing name, company_name etc.
    result = email_action.execute(lead_missing_fields, sample_qualification_result_qualified) # qual result doesn't matter much here

    assert "their company" in result['email_subject'] # Default placeholder
    assert "there" in result['email_body'] # Default placeholder for name
    assert "their company" in result['email_body'] # Default placeholder for company name
    assert "their industry" in result['email_body'] # Default placeholder for industry
    assert "their current size" in result['email_body'] # Default placeholder for size

# --- Tests for TagLeadInCRMAction ---

def test_tag_lead_in_crm_action_instance(tag_action: TagLeadInCRMAction, mock_crm_handler: MockCRMHandler):
    """Test TagLeadInCRMAction instantiation."""
    assert isinstance(tag_action, ActionHandlerBase)
    assert tag_action.crm_handler == mock_crm_handler

def test_tag_lead_in_crm_action_execute_unqualified(
    tag_action: TagLeadInCRMAction,
    mock_crm_handler: MockCRMHandler,
    sample_unqualified_lead: Dict[str, Any],
    sample_qualification_result_unqualified: Dict[str, Any]
):
    """Test TagLeadInCRMAction for an unqualified lead."""
    lead_email = sample_unqualified_lead['email']

    # Ensure lead exists in MockCRM for tagging (as main.py would do)
    mock_crm_handler.create_lead(sample_unqualified_lead)

    # Spy on CRM handler methods
    mock_crm_handler.update_lead_status = MagicMock(wraps=mock_crm_handler.update_lead_status)
    mock_crm_handler.add_note_to_lead = MagicMock(wraps=mock_crm_handler.add_note_to_lead)

    result = tag_action.execute(sample_unqualified_lead, sample_qualification_result_unqualified)

    assert result['action_type'] == 'crm_tag_action'
    assert result['lead_email'] == lead_email
    assert result['tag_applied'] == 'unqualified'
    assert result['reason'] == sample_qualification_result_unqualified['summary']
    assert f"Lead {lead_email} tagged as 'unqualified' in CRM." in result['status_message']

    # Verify CRM calls
    mock_crm_handler.update_lead_status.assert_called_once_with(
        lead_email,
        status='unqualified',
        details={'qualification_summary': sample_qualification_result_unqualified['summary']}
    )
    mock_crm_handler.add_note_to_lead.assert_called_once_with(
        lead_email,
        f"Lead marked as 'unqualified'. Reason: {sample_qualification_result_unqualified['summary']}"
    )

    # Check internal state of MockCRM (optional, but good for this mock)
    updated_crm_lead = mock_crm_handler.get_lead(lead_email)
    assert updated_crm_lead is not None
    assert updated_crm_lead.get('status') == 'unqualified'
    assert f"Lead marked as 'unqualified'. Reason: {sample_qualification_result_unqualified['summary']}" in updated_crm_lead.get('notes', [])


def test_tag_lead_in_crm_action_qualified_review_tag(
    tag_action: TagLeadInCRMAction,
    mock_crm_handler: MockCRMHandler,
    sample_qualified_lead: Dict[str, Any],
    sample_qualification_result_qualified: Dict[str, Any] # Lead is qualified
):
    """Test TagLeadInCRMAction if mistakenly called with a qualified lead (should use 'needs_manual_review' tag)."""
    lead_email = sample_qualified_lead['email']
    mock_crm_handler.create_lead(sample_qualified_lead)

    mock_crm_handler.update_lead_status = MagicMock(wraps=mock_crm_handler.update_lead_status)
    mock_crm_handler.add_note_to_lead = MagicMock(wraps=mock_crm_handler.add_note_to_lead)

    result = tag_action.execute(sample_qualified_lead, sample_qualification_result_qualified)

    assert result['action_type'] == 'crm_tag_action'
    assert result['tag_applied'] == 'needs_manual_review' # Important: tag for qualified leads if this action is (mis)used

    mock_crm_handler.update_lead_status.assert_called_once_with(
        lead_email,
        status='needs_manual_review',
        details={'qualification_summary': sample_qualification_result_qualified['summary']}
    )
    mock_crm_handler.add_note_to_lead.assert_called_once_with(
        lead_email,
        f"Lead marked as 'needs_manual_review'. Reason: {sample_qualification_result_qualified['summary']}"
    )


def test_tag_lead_in_crm_action_missing_email(tag_action: TagLeadInCRMAction):
    """Test TagLeadInCRMAction when lead email is missing."""
    lead_no_email = {'name': 'No Email User'}
    result = tag_action.execute(lead_no_email, sample_qualification_result_unqualified)

    assert result['action_type'] == 'crm_tag_failed'
    assert 'Lead email missing' in result['reason']


def test_tag_lead_in_crm_action_crm_failure(
    tag_action: TagLeadInCRMAction,
    mock_crm_handler: MockCRMHandler,
    sample_unqualified_lead: Dict[str, Any],
    sample_qualification_result_unqualified: Dict[str, Any]
):
    """Test TagLeadInCRMAction when CRM operations fail."""
    lead_email = sample_unqualified_lead['email']
    mock_crm_handler.create_lead(sample_unqualified_lead)

    # Simulate CRM failure by patching methods to return False
    with patch.object(mock_crm_handler, 'update_lead_status', return_value=False) as mock_update, \
         patch.object(mock_crm_handler, 'add_note_to_lead', return_value=True) as mock_add_note: # One success, one fail

        result = tag_action.execute(sample_unqualified_lead, sample_qualification_result_unqualified)

        assert result['action_type'] == 'crm_tag_failed'
        assert lead_email == result['lead_email']
        assert "CRM update failed. Status update: False, Note added: True" in result['reason']

        mock_update.assert_called_once()
        mock_add_note.assert_called_once()


if __name__ == '__main__':
    pytest.main()
