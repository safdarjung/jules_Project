import pytest
from typing import Dict, List, Any

from ai_sdr_assistant.lead_prospecting import SimpleWebSearchProspector, ProspectorBase
# It's often better to use a mock USER_PROFILE for testing to avoid dependency on exact values in settings.py
# However, for this simple prospector, using the actual one might be fine, or a fixture can provide one.

@pytest.fixture
def mock_user_profile() -> Dict[str, Any]:
    """Provides a mock USER_PROFILE for testing."""
    return {
        'my_company_name': "Test My Awesome Consulting Inc.",
        'services_offered': "Test AI strategy, custom machine learning model development.",
        'target_keywords': ["test enterprise software", "test SaaS solutions"],
        'target_industry': ["Test Technology", "Test Finance"],
        'target_company_size': ["10-50 employees", "50-200 employees"],
        'target_location': "Test Bay Area",
        'sdr_name': "Test AI SDR",
        'sdr_email': "test.aisdr@example.com"
    }

@pytest.fixture
def prospector() -> SimpleWebSearchProspector:
    """Provides a SimpleWebSearchProspector instance."""
    return SimpleWebSearchProspector()

def test_simple_web_search_prospector_instance(prospector: SimpleWebSearchProspector):
    """Test if SimpleWebSearchProspector can be instantiated."""
    assert isinstance(prospector, ProspectorBase)
    assert isinstance(prospector, SimpleWebSearchProspector)

def test_find_companies_returns_list_of_dicts(prospector: SimpleWebSearchProspector, mock_user_profile: Dict[str, Any]):
    """Test that find_companies returns a list of dictionaries."""
    companies = prospector.find_companies(user_profile=mock_user_profile)
    assert isinstance(companies, list)
    assert len(companies) > 0  # Expecting the hardcoded sample companies
    for company in companies:
        assert isinstance(company, dict)

def test_find_companies_output_structure(prospector: SimpleWebSearchProspector, mock_user_profile: Dict[str, Any]):
    """Test the structure of dictionaries returned by find_companies."""
    companies = prospector.find_companies(user_profile=mock_user_profile)
    for company in companies:
        assert 'company_name' in company
        assert isinstance(company['company_name'], str)
        assert 'website' in company
        assert isinstance(company['website'], str)
        assert 'source' in company
        assert company['source'] == 'simulated_web_search'

        assert 'industry_hint' in company
        assert isinstance(company['industry_hint'], str)

        assert 'location_hint' in company
        assert isinstance(company['location_hint'], str)

def test_find_companies_uses_user_profile_hints(prospector: SimpleWebSearchProspector, mock_user_profile: Dict[str, Any]):
    """Test if industry_hint and location_hint reflect the user_profile."""
    companies = prospector.find_companies(user_profile=mock_user_profile)

    # The SimpleWebSearchProspector's hardcoded data has some specific hints,
    # and some that directly use the user_profile.
    # Example: First company uses the first target_industry from user_profile
    if companies: # if list is not empty
        first_company = companies[0]
        if mock_user_profile.get('target_industry'):
            expected_industry_hint = mock_user_profile['target_industry'][0]
            assert first_company['industry_hint'] == expected_industry_hint

        expected_location_hint = mock_user_profile.get('target_location', "Unknown")
        # This check depends on how the sample data in SimpleWebSearchProspector is structured.
        # The sample data in SimpleWebSearchProspector uses user_profile.get('target_location', "Unknown") for all.
        assert first_company['location_hint'] == expected_location_hint

        # For 'CoreLogic Software', industry_hint is hardcoded to 'Software'
        corelogic_company = next((c for c in companies if c['company_name'] == 'CoreLogic Software'), None)
        if corelogic_company:
            assert corelogic_company['industry_hint'] == 'Software'


if __name__ == '__main__':
    pytest.main()
