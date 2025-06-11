import pytest
from typing import Dict, Any

from ai_sdr_assistant.lead_enrichment import SimpleCompanyInfoEnricher, LeadEnricherBase

@pytest.fixture
def enricher() -> SimpleCompanyInfoEnricher:
    """Provides a SimpleCompanyInfoEnricher instance for tests."""
    return SimpleCompanyInfoEnricher()

def test_simple_company_info_enricher_instance(enricher: SimpleCompanyInfoEnricher):
    """Test if SimpleCompanyInfoEnricher can be instantiated."""
    assert isinstance(enricher, LeadEnricherBase)
    assert isinstance(enricher, SimpleCompanyInfoEnricher)

def test_enrich_known_domain(enricher: SimpleCompanyInfoEnricher):
    """Test enrichment with a known domain (example.com)."""
    lead: Dict[str, str] = {'email': 'ceo@example.com', 'name': 'CEO Example'}
    enriched_lead: Dict[str, Any] = enricher.enrich(lead)

    assert enriched_lead['company_name'] == 'Example Corp'
    assert enriched_lead['industry'] == 'Software'
    assert enriched_lead['size'] == '50-200 employees'
    assert enriched_lead['domain'] == 'example.com'
    assert 'enrichment_notes' not in enriched_lead # No notes for successful enrichment of this type

def test_enrich_another_known_domain(enricher: SimpleCompanyInfoEnricher):
    """Test enrichment with another known domain (anothercorp.com)."""
    lead: Dict[str, str] = {'email': 'manager@anothercorp.com', 'name': 'Manager AC'}
    enriched_lead: Dict[str, Any] = enricher.enrich(lead)

    assert enriched_lead['company_name'] == 'Another Corp Ltd'
    assert enriched_lead['industry'] == 'Manufacturing'
    assert enriched_lead['size'] == '500+ employees'
    assert enriched_lead['domain'] == 'anothercorp.com'
    assert 'enrichment_notes' not in enriched_lead

def test_enrich_unknown_domain(enricher: SimpleCompanyInfoEnricher):
    """Test enrichment with an unknown domain."""
    lead: Dict[str, str] = {'email': 'info@unknowncompany.biz', 'name': 'Info UC'}
    enriched_lead: Dict[str, Any] = enricher.enrich(lead)

    # Check that original info is preserved
    assert enriched_lead['email'] == 'info@unknowncompany.biz'
    assert enriched_lead['name'] == 'Info UC'

    # Check that no dummy company data was added for unknown domain
    assert 'company_name' not in enriched_lead
    assert 'industry' not in enriched_lead
    assert 'size' not in enriched_lead

    # Check for enrichment notes
    assert 'enrichment_notes' in enriched_lead
    assert "Could not find company info for domain: unknowncompany.biz" in enriched_lead['enrichment_notes']

def test_enrich_invalid_email_format(enricher: SimpleCompanyInfoEnricher):
    """Test enrichment with an invalid email format."""
    lead: Dict[str, str] = {'email': 'invalid-email', 'name': 'Invalid User'}
    enriched_lead: Dict[str, Any] = enricher.enrich(lead)

    assert enriched_lead['email'] == 'invalid-email' # Original email preserved
    assert 'company_name' not in enriched_lead
    assert 'enrichment_notes' in enriched_lead
    assert "Invalid email format, cannot extract domain." in enriched_lead['enrichment_notes']

def test_enrich_missing_email(enricher: SimpleCompanyInfoEnricher):
    """Test enrichment when the email field is missing."""
    lead: Dict[str, str] = {'name': 'No Email User'} # No 'email' key
    enriched_lead: Dict[str, Any] = enricher.enrich(lead)

    assert 'email' not in enriched_lead
    assert 'company_name' not in enriched_lead
    assert 'enrichment_notes' in enriched_lead
    assert "No email provided for enrichment." in enriched_lead['enrichment_notes']

def test_enrich_empty_email_string(enricher: SimpleCompanyInfoEnricher):
    """Test enrichment with an empty email string."""
    lead: Dict[str, str] = {'email': '', 'name': 'Empty Email String User'}
    enriched_lead: Dict[str, Any] = enricher.enrich(lead)

    assert enriched_lead['email'] == ''
    assert 'company_name' not in enriched_lead
    assert 'enrichment_notes' in enriched_lead
    # An empty email string `''` will trigger the 'No email provided' path
    assert "No email provided for enrichment." in enriched_lead['enrichment_notes']

if __name__ == '__main__':
    pytest.main()
