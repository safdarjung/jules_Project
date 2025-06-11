from typing import List, Dict, Any
import logging

# Configure basic logging
# LOG_LEVEL can be imported from settings if defined there, otherwise set directly
# from .config.settings import LOG_LEVEL, LOG_FORMAT # Assuming these might be in settings
LOG_FORMAT_STRING = "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT_STRING) # Default to INFO if not from settings

# Import necessary classes from the SDR assistant modules
from .lead_prospecting.prospector import SimpleWebSearchProspector, ProspectorBase
from .lead_ingestion import WebsiteFormIngestor, LeadIngestorBase
from .lead_enrichment import SimpleCompanyInfoEnricher, LeadEnricherBase
from .lead_qualification import ICPQualifier, LeadQualifierBase
from .action import EmailDraftAction, TagLeadInCRMAction, ActionHandlerBase
from .crm import MockCRMHandler, CRMHandlerBase
from .config.settings import IDEAL_CUSTOMER_PROFILE, USER_PROFILE # Import both profiles

def run_sdr_workflow():
    """
    Runs the main outbound Sales Development Representative (SDR) workflow.
    This includes prospecting for companies, ingesting them as leads,
    enriching, qualifying, and dispatching actions.
    """
    logging.info("Starting OUTBOUND SDR workflow...")
    logging.info(f"User Profile Loaded: Operating as {USER_PROFILE.get('my_company_name')} targeting {USER_PROFILE.get('target_industry')}")

    # 1. Instantiate services
    logging.info("Initializing services for outbound workflow...")

    # Prospecting service
    prospector: ProspectorBase = SimpleWebSearchProspector()

    # Lead Ingestion service - now takes a prospector
    ingestor: LeadIngestorBase = WebsiteFormIngestor(prospector=prospector) # USER_PROFILE is used internally by ingestor

    # Enrichment and Qualification services
    enricher: LeadEnricherBase = SimpleCompanyInfoEnricher()
    qualifier: LeadQualifierBase = ICPQualifier(icp_criteria=IDEAL_CUSTOMER_PROFILE)

    # CRM and Action Handlers
    crm_handler: CRMHandlerBase = MockCRMHandler() # Initialize CRM Handler
    # Ensure CRM handler is initialized before creating leads, so actions can use it.
    # Initialize all leads found by prospector in CRM
    initial_companies_for_crm = prospector.find_companies(user_profile=USER_PROFILE)
    logging.info(f"Pre-populating CRM with {len(initial_companies_for_crm)} prospected companies for tracking...")
    for company_data in initial_companies_for_crm:
        # Minimal data for CRM creation initially. More details can be added after enrichment.
        # The ingestor will generate a placeholder email if not present.
        base_crm_lead: Dict[str, Any] = {
            'company_name': company_data.get('company_name'),
            'website': company_data.get('website'),
            'email': f"contact@{company_data.get('website', '').replace('www.','')}" if company_data.get('website') else f"contact@{company_data.get('company_name','unknown').lower().replace(' ','')}.example.com",
            'status': 'prospected',
            'source': company_data.get('source', 'unknown_prospector')
        }
        if not crm_handler.get_lead(base_crm_lead['email']):
            crm_handler.create_lead(base_crm_lead)
        else:
            logging.info(f"Company {base_crm_lead['company_name']} with email {base_crm_lead['email']} already in CRM.")


    email_action: ActionHandlerBase = EmailDraftAction(
        sdr_name=USER_PROFILE.get('sdr_name', "AI SDR"),
        your_company_name=USER_PROFILE.get('my_company_name', "Our Company"),
        product_service_name=USER_PROFILE.get('services_offered', "our innovative solution") # Use services from USER_PROFILE
    )
    crm_tag_action: ActionHandlerBase = TagLeadInCRMAction(crm_handler=crm_handler)

    logging.info("Services initialized.")

    # 2. Process leads (Ingestor now handles prospecting)
    logging.info("Ingesting leads (prospecting is part of this step)...")
    # The ingestor.ingest() method now uses the prospector and USER_PROFILE internally
    raw_leads: List[Dict[str, Any]] = ingestor.ingest()
    logging.info(f"Ingested {len(raw_leads)} new leads from prospecting.")

    if not raw_leads:
        logging.info("No new leads to process from prospecting. Exiting workflow.")
        return

    for i, lead_data in enumerate(raw_leads): # Changed raw_lead to lead_data for clarity
        logging.info(f"\n--- Processing Lead {i+1}/{len(raw_leads)}: {lead_data.get('company_name')} ({lead_data.get('email')}) ---")

        lead_email = lead_data.get('email')

        # Enrich lead
        logging.info(f"Enriching lead: {lead_data.get('company_name')}")
        enriched_lead: Dict[str, Any] = enricher.enrich(lead_data)
        logging.info(f"Enriched lead data: {enriched_lead}")
        if lead_email:
            # Update CRM with enriched data, ensure 'status' is not overwritten if already meaningful
            crm_lead_update = enriched_lead.copy()
            existing_crm_lead = crm_handler.get_lead(lead_email)
            if existing_crm_lead and existing_crm_lead.get('status') not in [None, 'prospected', 'new']:
                 crm_lead_update['status'] = existing_crm_lead.get('status') # Preserve more advanced status
            else:
                 crm_lead_update.setdefault('status', "enriched")
            crm_handler.update_lead_status(lead_email, crm_lead_update['status'], crm_lead_update)


        # Qualify lead
        logging.info(f"Qualifying lead: {enriched_lead.get('company_name')}")
        qualification_result: Dict[str, Any] = qualifier.qualify(enriched_lead)
        logging.info(f"Qualification result: {qualification_result}")

        # Dispatch action based on qualification
        action_taken: Dict[str, Any]
        if qualification_result.get('qualified'):
            logging.info(f"Lead QUALIFIED. Executing email draft action for: {enriched_lead.get('company_name')}")
            action_taken = email_action.execute(enriched_lead, qualification_result)
            logging.info(f"Email Draft Action executed. Result: {action_taken.get('status_message')}")
            print("\n--- Drafted Email ---")
            print(f"To: {action_taken.get('lead_email')}")
            print(f"Subject: {action_taken.get('email_subject')}")
            print(f"Body:\n{action_taken.get('email_body')}\n")

            if lead_email:
                crm_handler.add_note_to_lead(
                    lead_email,
                    f"Qualified. Email drafted. Subject: '{action_taken.get('email_subject')}'"
                )
                crm_handler.update_lead_status(lead_email, "contact_pending_approval", {"last_action": "email_drafted", "qualification_summary": qualification_result.get('summary')})

        else:
            logging.info(f"Lead NOT QUALIFIED. Executing CRM tag action for: {enriched_lead.get('company_name')}")
            # TagLeadInCRMAction already updates CRM status and adds notes
            action_taken = crm_tag_action.execute(enriched_lead, qualification_result)
            logging.info(f"CRM Tag Action executed. Result: {action_taken.get('status_message')}")

        logging.info(f"--- Finished processing Lead {i+1}/{len(raw_leads)} ({enriched_lead.get('company_name')}) ---")

    logging.info("Outbound SDR workflow completed.")

if __name__ == '__main__':
    run_sdr_workflow()
