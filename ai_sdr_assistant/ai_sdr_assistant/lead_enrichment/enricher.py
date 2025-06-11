from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urlparse

class LeadEnricherBase(ABC):
    """
    Base class for lead enrichment.
    """
    @abstractmethod
    def enrich(self, lead: Dict[str, Any]) -> Dict[str, Any]: # Changed to Dict[str, Any]
        """
        Abstract method to enrich a lead.
        Takes a lead dictionary and returns an enriched lead dictionary.
        """
        pass

class SimpleCompanyInfoEnricher(LeadEnricherBase):
    """
    Placeholder for enriching leads with company information.
    Simulates fetching company data based on website or email domain.
    """

    def _extract_domain(self, lead: Dict[str, Any]) -> Optional[str]:
        """
        Extracts a domain from the lead's website or email.
        Prioritizes website, then email. Handles basic URL parsing.
        """
        website_url = lead.get('website')
        email = lead.get('email')
        domain: Optional[str] = None

        # Try website first
        if website_url:
            try:
                # Add scheme if missing for urlparse to work correctly
                if not website_url.startswith(('http://', 'https://')):
                    website_url = 'http://' + website_url

                parsed_url = urlparse(website_url)
                if parsed_url.netloc:
                    domain = parsed_url.netloc.replace('www.', '') # Remove www.
            except Exception as e: # Catch any parsing errors
                print(f"Enricher: Error parsing website URL '{website_url}': {e}")
                # Fall through to try email if website parsing fails

        # If domain not found from website, or if email is not generic, try email
        if not domain and email:
            # Heuristic: if email is generic, website domain (if available and different) might be better.
            # However, if website parsing failed or no website, email is the only option.
            is_generic_email = email.startswith(('info@', 'contact@', 'hello@', 'sales@', 'admin@'))

            if not website_url or not domain or not is_generic_email: # If no website, or website domain failed, or email is not generic
                try:
                    email_domain = email.split('@')[1]
                    domain = email_domain # Prefer email domain if it's specific
                except IndexError:
                    # Invalid email format
                    return None # Cannot extract domain from email either

        return domain


    def enrich(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches a lead with dummy company information based on extracted domain.
        Preserves existing information like company_name from prospector if no new info is "found".
        """
        # Placeholder for actual company data lookup (e.g., Clearbit API, web scraping)
        enriched_lead = lead.copy() # Start with a copy of the lead

        domain = self._extract_domain(enriched_lead)
        enriched_lead['extracted_domain'] = domain # Store the extracted domain for transparency

        if not domain:
            enriched_lead['enrichment_notes'] = lead.get('enrichment_notes', "") + " Could not determine a valid domain from website or email."
            # If there's an industry_hint from prospector, use it
            if 'industry_hint' in lead and 'industry' not in enriched_lead:
                enriched_lead['industry'] = lead['industry_hint']
            return enriched_lead

        # Simulated data lookup based on domain
        # Preserve prospector's company_name if enricher doesn't find a "better" one.
        # For this simple version, we'll add new fields if they don't conflict.

        company_data_found = False
        # Order matters: check for more specific subdomains before general ones.
        if "innovatech.example.com" in domain: # From new prospector data
            enriched_lead.setdefault('company_name', 'Innovatech Solutions (Enriched)')
            enriched_lead.setdefault('industry', lead.get('industry_hint', 'Technology'))
            enriched_lead.setdefault('size', '100-300 Tech Employees')
            company_data_found = True
        elif "quantumleap.example.com" in domain: # From new prospector data
            enriched_lead.setdefault('company_name', 'QuantumLeap AI (Enriched)')
            enriched_lead.setdefault('industry', lead.get('industry_hint', 'AI Research'))
            enriched_lead.setdefault('size', '20-80 AI Specialists')
            company_data_found = True
        elif "synergysystems.example.com" in domain: # From new prospector data
            enriched_lead.setdefault('company_name', 'Synergy Systems Ltd. (Enriched)')
            enriched_lead.setdefault('industry', lead.get('industry_hint', 'Consulting Services'))
            enriched_lead.setdefault('size', 'Large Enterprise Solutions')
            company_data_found = True
        elif "corelogic.example.com" in domain: # From new prospector data
            enriched_lead.setdefault('company_name', lead.get('company_name', 'CoreLogic Software (Enriched)')) # Use prospector's name if available
            enriched_lead.setdefault('industry', lead.get('industry_hint', 'Software Development'))
            enriched_lead.setdefault('size', 'Unknown Size - Software Focus')
            company_data_found = True
        elif "example.com" in domain: # General example.com should be checked after specific subdomains
            enriched_lead.setdefault('company_name', 'Example Corp') # setdefault preserves existing value
            enriched_lead.setdefault('industry', 'Software')
            enriched_lead.setdefault('size', '50-200 employees')
            company_data_found = True
        elif "anothercorp.com" in domain:
            enriched_lead.setdefault('company_name', 'Another Corp Ltd')
            enriched_lead.setdefault('industry', 'Manufacturing')
            enriched_lead.setdefault('size', '500+ employees')
            company_data_found = True

        if company_data_found:
            current_notes = lead.get('enrichment_notes', "")
            enriched_lead['enrichment_notes'] = (current_notes + " " if current_notes else "") + f"Simulated data found for domain: {domain}."
        else:
            # If no specific data found for the domain, but domain was extracted
            current_notes = lead.get('enrichment_notes', "")
            enriched_lead['enrichment_notes'] = (current_notes + " " if current_notes else "") + f"Domain '{domain}' extracted, but no specific company simulation data found."
            # Use hints if available and fields not already set
            if 'industry_hint' in lead and 'industry' not in enriched_lead:
                enriched_lead['industry'] = lead['industry_hint']
            if 'location_hint' in lead and 'location' not in enriched_lead:
                 enriched_lead['location'] = lead['location_hint']


        return enriched_lead

if __name__ == '__main__':
    enricher = SimpleCompanyInfoEnricher()

    print("--- Testing Enrichment Scenarios ---")

    # Scenario 1: Lead from prospector with website, generic email, and hints
    lead_from_prospector1 = {
        'email': 'info@innovatech.example.com',
        'name': 'Contact at Innovatech Solutions',
        'company_name': 'Innovatech Solutions', # From prospector
        'website': 'innovatech.example.com',
        'source': 'simulated_web_search',
        'industry_hint': 'Technology',
        'location_hint': 'Silicon Valley'
    }
    enriched1 = enricher.enrich(lead_from_prospector1)
    print(f"\n1. Lead from Prospector (Innovatech): {lead_from_prospector1}")
    print(f"   Enriched: {enriched1}")
    assert enriched1.get('industry') == 'Technology' # Should use hint or enriched default
    assert enriched1.get('company_name') == 'Innovatech Solutions (Enriched)' # Enriched version
    assert enriched1.get('extracted_domain') == 'innovatech.example.com'

    # Scenario 2: Lead with only email (known domain in simulation)
    lead_email_only_known = {'email': 'jdoe@example.com', 'name': 'John Doe'}
    enriched2 = enricher.enrich(lead_email_only_known)
    print(f"\n2. Lead with Email Only (example.com): {lead_email_only_known}")
    print(f"   Enriched: {enriched2}")
    assert enriched2.get('company_name') == 'Example Corp'
    assert enriched2.get('industry') == 'Software'
    assert enriched2.get('extracted_domain') == 'example.com'

    # Scenario 3: Lead with website (unknown domain in simulation) and specific email
    lead_website_unknown_specific_email = {
        'email': 'jane.doe@newstartup.io',
        'name': 'Jane Doe - New Startup',
        'company_name': 'New Startup Inc.',
        'website': 'www.newstartup.io',
        'industry_hint': 'Fintech'
    }
    enriched3 = enricher.enrich(lead_website_unknown_specific_email)
    print(f"\n3. Lead with Website (newstartup.io) & Specific Email: {lead_website_unknown_specific_email}")
    print(f"   Enriched: {enriched3}")
    assert enriched3.get('extracted_domain') == 'newstartup.io'
    assert enriched3.get('industry') == 'Fintech' # Should use hint as no simulation data for newstartup.io
    assert enriched3.get('company_name') == 'New Startup Inc.' # Original preserved
    assert "no specific company simulation data found" in enriched3.get('enrichment_notes', "")

    # Scenario 4: Lead with no email and no website
    lead_no_contact_info = {'name': 'Mystery Guest', 'company_name': 'Mystery LLC'}
    enriched4 = enricher.enrich(lead_no_contact_info)
    print(f"\n4. Lead with No Contact Info: {lead_no_contact_info}")
    print(f"   Enriched: {enriched4}")
    assert enriched4.get('extracted_domain') is None
    assert "Could not determine a valid domain" in enriched4.get('enrichment_notes', "")

    # Scenario 5: Lead with website that might cause parsing issues (e.g. just a name)
    lead_bad_website = {
        'email': 'info@badsite.com',
        'name': 'Bad Site Contact',
        'company_name': 'Bad Site Co',
        'website': 'NotAUrl'
    }
    enriched5 = enricher.enrich(lead_bad_website)
    print(f"\n5. Lead with Bad Website String: {lead_bad_website}")
    print(f"   Enriched: {enriched5}")
    # Domain extraction from 'NotAUrl' might become 'notaurl' if http:// is prepended.
    # If it's not in simulated data, it will use email domain if possible.
    assert enriched5.get('extracted_domain') == 'badsite.com' # Falls back to email domain
    assert "no specific company simulation data found" in enriched5.get('enrichment_notes', "")

    # Scenario 6: Lead with generic email and website for a known domain
    lead_generic_email_known_site = {
        'email': 'info@example.com', # Generic email
        'name': 'Info Example',
        'company_name': 'Example By Email', # Prospector might provide this
        'website': 'www.example.com' # Website is for a known domain
    }
    enriched6 = enricher.enrich(lead_generic_email_known_site)
    print(f"\n6. Lead with Generic Email and Known Website: {lead_generic_email_known_site}")
    print(f"   Enriched: {enriched6}")
    assert enriched6.get('extracted_domain') == 'example.com' # Should prefer website domain
    assert enriched6.get('company_name') == 'Example By Email' # Prospector's name preserved by setdefault
    assert enriched6.get('industry') == 'Software' # Enriched
    assert enriched6.get('size') == '50-200 employees' # Enriched

    # Scenario 7: Lead with only company_name and website (simulating output from new ingestor)
    lead_from_ingestor_basic = {
        'company_name': 'CoreLogic Software',
        'website': 'corelogic.example.com',
        'email': 'info@corelogic.example.com', # Added by ingestor
        'name': 'Contact at CoreLogic Software', # Added by ingestor
        'source': 'simulated_web_search',
        'industry_hint': 'Software' # Added by prospector
    }
    enriched7 = enricher.enrich(lead_from_ingestor_basic)
    print(f"\n7. Lead from Ingestor (CoreLogic): {lead_from_ingestor_basic}")
    print(f"   Enriched: {enriched7}")
    assert enriched7.get('company_name') == 'CoreLogic Software' # Preserved from prospector
    assert enriched7.get('industry') == 'Software' # Used hint or enriched value
    assert "Simulated data found for domain: corelogic.example.com" in enriched7.get('enrichment_notes', "")

    print("\nEnrichment tests completed.")
