from typing import List, Dict, Any
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import necessary classes from the SDR assistant modules
from .lead_ingestion import WebsiteFormIngestor, LeadIngestorBase
from .lead_enrichment import SimpleCompanyInfoEnricher, LeadEnricherBase
from .lead_qualification import ICPQualifier, LeadQualifierBase
from .action import EmailDraftAction, TagLeadInCRMAction, ActionHandlerBase
from .crm import MockCRMHandler, CRMHandlerBase
from .config.settings import IDEAL_CUSTOMER_PROFILE

def run_sdr_workflow():
    """
    Runs the main Sales Development Representative (SDR) workflow.
    This includes ingesting, enriching, qualifying leads, and dispatching actions.
    """
    logging.info("Starting SDR workflow...")

    # 1. Instantiate services
    logging.info("Initializing services...")
    ingestor: LeadIngestorBase = WebsiteFormIngestor()
    enricher: LeadEnricherBase = SimpleCompanyInfoEnricher()
    qualifier: LeadQualifierBase = ICPQualifier(icp_criteria=IDEAL_CUSTOMER_PROFILE)

    # CRM and Action Handlers
    crm_handler: CRMHandlerBase = MockCRMHandler()
    email_action: ActionHandlerBase = EmailDraftAction(
        sdr_name="Alex the AI SDR",
        your_company_name="Innovatech Solutions",
        product_service_name="our cutting-edge AI platform"
    )
    crm_tag_action: ActionHandlerBase = TagLeadInCRMAction(crm_handler=crm_handler)

    logging.info("Services initialized.")

    # 2. Process leads
    logging.info("Ingesting leads...")
    raw_leads: List[Dict[str, str]] = ingestor.ingest()
    logging.info(f"Ingested {len(raw_leads)} raw leads.")

    if not raw_leads:
        logging.info("No leads to process. Exiting workflow.")
        return

    for i, raw_lead in enumerate(raw_leads):
        logging.info(f"\n--- Processing Lead {i+1}/{len(raw_leads)}: {raw_lead.get('email', 'N/A')} ---")

        # Ensure lead exists in CRM (or create it)
        # This helps actions like TagLeadInCRMAction to find the lead.
        lead_email = raw_lead.get('email')
        if lead_email:
            if not crm_handler.get_lead(lead_email):
                crm_handler.create_lead(raw_lead) # Create if not exists
        else:
            logging.warning(f"Lead {raw_lead.get('name', 'Unknown')} has no email, skipping CRM check/creation.")
            # Decide if you want to skip processing entirely or proceed with enrichment/qualification
            # For now, we'll proceed but CRM dependent actions might fail or log warnings.

        # Enrich lead
        logging.info(f"Enriching lead: {raw_lead.get('email', raw_lead.get('name', 'N/A'))}")
        enriched_lead: Dict[str, Any] = enricher.enrich(raw_lead)
        logging.info(f"Enriched lead data: {enriched_lead}")
        if lead_email: # Update CRM with enriched data if email exists
            crm_handler.update_lead_status(lead_email, "enriched", enriched_lead)


        # Qualify lead
        logging.info(f"Qualifying lead: {enriched_lead.get('email', enriched_lead.get('name', 'N/A'))}")
        qualification_result: Dict[str, Any] = qualifier.qualify(enriched_lead)
        logging.info(f"Qualification result: {qualification_result}")

        # Dispatch action based on qualification
        action_taken: Dict[str, Any]
        if qualification_result.get('qualified'):
            logging.info(f"Lead qualified. Executing email draft action for: {enriched_lead.get('email')}")
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
                crm_handler.update_lead_status(lead_email, "contact_pending_approval", {"last_action": "email_drafted"})

        else:
            logging.info(f"Lead not qualified. Executing CRM tag action for: {enriched_lead.get('email')}")
            action_taken = crm_tag_action.execute(enriched_lead, qualification_result)
            logging.info(f"CRM Tag Action executed. Result: {action_taken.get('status_message')}")

        logging.info(f"--- Finished processing Lead {i+1}/{len(raw_leads)} ---")

    logging.info("SDR workflow completed.")

if __name__ == '__main__':
    run_sdr_workflow()
