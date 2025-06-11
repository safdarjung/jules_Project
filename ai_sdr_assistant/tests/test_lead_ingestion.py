import pytest
from typing import List, Dict, Any

from ai_sdr_assistant.lead_ingestion import WebsiteFormIngestor, LeadIngestorBase

def test_website_form_ingestor_instance():
    """Test if WebsiteFormIngestor can be instantiated."""
    ingestor = WebsiteFormIngestor()
    assert isinstance(ingestor, LeadIngestorBase)
    assert isinstance(ingestor, WebsiteFormIngestor)

def test_website_form_ingestor_ingest():
    """Test the ingest() method of WebsiteFormIngestor."""
    ingestor = WebsiteFormIngestor()
    leads: List[Dict[str, str]] = ingestor.ingest()

    assert isinstance(leads, list)
    assert len(leads) > 0  # Expecting at least one sample lead

    for lead in leads:
        assert isinstance(lead, dict)
        assert 'email' in lead
        assert isinstance(lead['email'], str)
        assert '@' in lead['email'] # Basic email format check
        assert 'name' in lead
        assert isinstance(lead['name'], str)

    # Check specific sample data if necessary (optional, as it's hardcoded)
    expected_sample_leads: List[Dict[str, str]] = [
        {'email': 'test1@example.com', 'name': 'Test User One'},
        {'email': 'test2@example.com', 'name': 'Test User Two'},
    ]
    assert leads == expected_sample_leads, "Sample data does not match expected structure."

if __name__ == '__main__':
    pytest.main()
