from abc import ABC, abstractmethod
from typing import Dict

class LeadEnricherBase(ABC):
    """
    Base class for lead enrichment.
    """
    @abstractmethod
    def enrich(self, lead: Dict[str, str]) -> Dict[str, str]:
        """
        Abstract method to enrich a lead.
        Takes a lead dictionary and returns an enriched lead dictionary.
        """
        pass

class SimpleCompanyInfoEnricher(LeadEnricherBase):
    """
    Placeholder for enriching leads with company information.
    """
    def enrich(self, lead: Dict[str, str]) -> Dict[str, str]:
        """
        Enriches a lead with dummy company information.
        Simulates fetching company data based on email domain.
        """
        # Placeholder for actual company data lookup (e.g., Clearbit API, web scraping)
        enriched_lead = lead.copy()
        email = lead.get('email')

        if email:
            try:
                domain = email.split('@')[1]
                # Simulate fetching data based on domain
                if "example.com" in domain: # Domain for sample leads
                    enriched_lead.update({
                        'company_name': 'Example Corp',
                        'industry': 'Software',
                        'size': '50-200 employees',
                        'domain': domain
                    })
                elif "anothercorp.com" in domain: # Another example
                     enriched_lead.update({
                        'company_name': 'Another Corp Ltd',
                        'industry': 'Manufacturing',
                        'size': '500+ employees',
                        'domain': domain
                    })
                else: # Domain not recognized for dummy data
                    enriched_lead['enrichment_notes'] = f"Could not find company info for domain: {domain}"
            except IndexError:
                # Invalid email format
                enriched_lead['enrichment_notes'] = "Invalid email format, cannot extract domain."
        else:
            enriched_lead['enrichment_notes'] = "No email provided for enrichment."

        return enriched_lead
