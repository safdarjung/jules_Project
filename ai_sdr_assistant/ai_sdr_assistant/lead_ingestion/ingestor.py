from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Import for the new prospecting capability
from ..lead_prospecting.prospector import ProspectorBase, SimpleWebSearchProspector
from ..config.settings import USER_PROFILE


class LeadIngestorBase(ABC):
    """
    Base class for lead ingestion.
    """
    @abstractmethod
    def ingest(self) -> List[Dict[str, Any]]: # Return type changed to List[Dict[str, Any]]
        """
        Abstract method to ingest leads.
        Should be implemented by subclasses.
        Returns a list of lead objects (dictionaries).
        """
        pass

class WebsiteFormIngestor(LeadIngestorBase):
    """
    Ingests leads, potentially originating from prospected companies.
    Previously, this was a placeholder for website form submissions.
    Now, it uses a Prospector to find companies and then transforms them into leads.
    """
    def __init__(self, prospector: Optional[ProspectorBase] = None):
        """
        Initializes the ingestor.

        Args:
            prospector: An instance of a ProspectorBase subclass.
                        If None, defaults to SimpleWebSearchProspector.
        """
        if prospector is None:
            self.prospector: ProspectorBase = SimpleWebSearchProspector()
        else:
            self.prospector: ProspectorBase = prospector

        # Store user_profile for use in ingest method
        self.user_profile: Dict[str, Any] = USER_PROFILE

    def ingest(self) -> List[Dict[str, Any]]:
        """
        Ingests leads by first finding companies using the prospector,
        then transforming company data into lead dictionaries.
        """
        print(f"Ingestor: Finding companies using {self.prospector.__class__.__name__}...")
        companies: List[Dict[str, str]] = self.prospector.find_companies(user_profile=self.user_profile)

        transformed_leads: List[Dict[str, Any]] = []

        if not companies:
            print("Ingestor: No companies found by the prospector.")
            return transformed_leads

        print(f"Ingestor: Found {len(companies)} companies. Transforming them into leads...")

        for company_dict in companies:
            website = company_dict.get('website')
            company_name = company_dict.get('company_name', 'Unknown Company')

            # Generate placeholder email and name
            # In a real scenario, finding actual contact persons would be a separate, complex step.
            placeholder_email = f"info@{website}" if website else f"info@{company_name.lower().replace(' ', '')}.example.com"
            placeholder_name = f"Contact at {company_name}"

            lead_data: Dict[str, Any] = {
                'email': placeholder_email,
                'name': placeholder_name,
                'company_name': company_name,
                'website': website,
                # Carry over any other fields from the prospector
                **company_dict # This will include 'source', 'industry_hint', 'location_hint', etc.
            }
            transformed_leads.append(lead_data)
            print(f"Ingestor: Transformed company '{company_name}' into lead: {lead_data.get('email')}")

        # The old hardcoded list of leads:
        # sample_leads: List[Dict[str, str]] = [
        #     {'email': 'test1@example.com', 'name': 'Test User One'},
        #     {'email': 'test2@example.com', 'name': 'Test User Two'},
        # ]
        # return sample_leads

        return transformed_leads

if __name__ == '__main__':
    # Example Usage:
    # This demonstrates how the WebsiteFormIngestor now uses a prospector.

    # Using the default SimpleWebSearchProspector
    print("--- Testing Ingestor with default SimpleWebSearchProspector ---")
    ingestor_default = WebsiteFormIngestor()
    leads_from_default = ingestor_default.ingest()
    print(f"\nIngested {len(leads_from_default)} leads (default prospector):")
    for lead in leads_from_default:
        print(lead)

    # Example with a custom (mock) prospector if needed for testing:
    class MockProspector(ProspectorBase):
        def find_companies(self, user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
            print(f"MockProspector: Finding companies with profile for {user_profile.get('my_company_name')}")
            return [
                {'company_name': 'Mocked Company A', 'website': 'mocka.example.com', 'source': 'mock_prospector'},
                {'company_name': 'Mocked Company B', 'website': 'mockb.example.com', 'source': 'mock_prospector'}
            ]

    print("\n--- Testing Ingestor with MockProspector ---")
    mock_prospector_instance = MockProspector()
    ingestor_custom = WebsiteFormIngestor(prospector=mock_prospector_instance)
    leads_from_custom = ingestor_custom.ingest()
    print(f"\nIngested {len(leads_from_custom)} leads (custom prospector):")
    for lead in leads_from_custom:
        print(lead)
