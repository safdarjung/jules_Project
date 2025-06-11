from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Import CRM handler to be used by actions
from ai_sdr_assistant.crm.crm_handler import CRMHandlerBase, MockCRMHandler

class ActionHandlerBase(ABC):
    """
    Base class for action handlers.
    """
    @abstractmethod
    def execute(self, lead: Dict[str, Any], qualification_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Abstract method to execute an action for a lead.
        Takes the lead data and its qualification result.
        Returns a dictionary describing the action taken.
        """
        pass

class EmailDraftAction(ActionHandlerBase):
    """
    Action handler for drafting personalized emails to qualified leads.
    """
    def __init__(self, sdr_name: str = "AI SDR", your_company_name: str = "Our Company", product_service_name: str = "innovative solution"):
        self.sdr_name = sdr_name
        self.your_company_name = your_company_name
        self.product_service_name = product_service_name
        # In a real system, SDR assignment might be more complex (e.g., round-robin, territory-based)
        self.assigned_sdr_email = "human_sdr_placeholder@example.com"

    def execute(self, lead: Dict[str, Any], qualification_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Drafts a personalized email to a qualified lead.
        """
        company_name = lead.get('company_name', 'their company')
        lead_name = lead.get('name', 'there')
        industry = lead.get('industry', 'their industry')
        size = lead.get('size', 'their current size')

        # Basic templating.
        # In a real system, this might use more sophisticated templating engines (e.g., Jinja2)
        # or AI-powered content generation.

        subject = f"Interesting Opportunity for {company_name}"

        body_parts = [
            f"Hi {lead_name},\n",
            f"I came across {company_name} and was impressed by your work in the {industry} space.",
            f"Given your company size of {size}, I thought our {self.product_service_name} could be a great fit for your team."
        ]

        # Placeholder for further personalization based on news/enrichment
        # E.g., if 'recent_news' in lead: body_parts.append(f"I also saw your recent news about {lead['recent_news']}.")

        body_parts.append("\nWould you be open to a brief chat next week to explore this further?\n")
        body_parts.append(f"Best regards,\n{self.sdr_name}\n{self.your_company_name}")

        email_body = "\n".join(body_parts)

        return {
            'action_type': 'email_drafted',
            'lead_email': lead.get('email'),
            'email_subject': subject,
            'email_body': email_body,
            'assigned_to_sdr': self.assigned_sdr_email,
            'status_message': f"Email drafted for {lead.get('email')} to {company_name}."
        }

class TagLeadInCRMAction(ActionHandlerBase):
    """
    Action handler for tagging unqualified leads in the CRM.
    """
    def __init__(self, crm_handler: CRMHandlerBase):
        self.crm_handler = crm_handler

    def execute(self, lead: Dict[str, Any], qualification_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Tags an unqualified lead in the CRM.
        """
        lead_email = lead.get('email')
        if not lead_email:
            return {
                'action_type': 'crm_tag_failed',
                'reason': 'Lead email missing, cannot tag in CRM.',
                'status_message': 'Failed to tag lead: email missing.'
            }

        tag = 'unqualified'
        reason_summary = "No qualification data provided."
        if qualification_result:
            reason_summary = qualification_result.get('summary', 'Reason not specified.')
            if qualification_result.get('qualified', True): # Should be False for this action
                tag = 'needs_manual_review' # Or some other appropriate tag

        # Update status in CRM
        status_updated = self.crm_handler.update_lead_status(
            lead_email,
            status=tag,
            details={'qualification_summary': reason_summary}
        )

        # Add a note
        note_added = self.crm_handler.add_note_to_lead(
            lead_email,
            f"Lead marked as '{tag}'. Reason: {reason_summary}"
        )

        if status_updated and note_added:
            return {
                'action_type': 'crm_tag_action',
                'lead_email': lead_email,
                'tag_applied': tag,
                'reason': reason_summary,
                'status_message': f"Lead {lead_email} tagged as '{tag}' in CRM. Reason: {reason_summary}"
            }
        else:
            return {
                'action_type': 'crm_tag_failed',
                'lead_email': lead_email,
                'reason': f"CRM update failed. Status update: {status_updated}, Note added: {note_added}",
                'status_message': f"Failed to fully tag {lead_email} in CRM."
            }

# Example usage (can be removed or kept for testing)
if __name__ == '__main__':
    # Sample lead data
    qualified_lead_example = {
        'email': 'ceo@example.com',
        'name': 'Jane Doe',
        'company_name': 'Example Corp',
        'industry': 'Software',
        'size': '100-250 employees'
    }
    unqualified_lead_example = {
        'email': 'contact@smallbiz.com',
        'name': 'John Smith',
        'company_name': 'Small Biz Ltd',
        'industry': 'Retail',
        'size': '1-10 employees'
    }
    qualification_for_unqualified = {
        'qualified': False,
        'summary': "Industry 'Retail' does not match required 'Software'. Company size '1' (from '1-10 employees') does not meet minimum of '50'."
    }

    # Email Draft Action
    email_action = EmailDraftAction(sdr_name="BDR Bot", your_company_name="AI Solutions Inc.", product_service_name="next-gen AI platform")
    email_result = email_action.execute(qualified_lead_example)
    print("--- Email Draft Action Result ---")
    print(f"To: {email_result.get('lead_email')}")
    print(f"Subject: {email_result.get('email_subject')}")
    print(f"Body:\n{email_result.get('email_body')}")
    print(f"Assigned SDR: {email_result.get('assigned_to_sdr')}")
    print(f"Status: {email_result.get('status_message')}\n")

    # Tag Lead In CRM Action
    mock_crm = MockCRMHandler()
    # Create lead in mock CRM first so it can be tagged
    mock_crm.create_lead(unqualified_lead_example)

    tag_action = TagLeadInCRMAction(crm_handler=mock_crm)
    tag_result = tag_action.execute(unqualified_lead_example, qualification_for_unqualified)
    print("--- Tag Lead In CRM Action Result ---")
    print(f"Action Type: {tag_result.get('action_type')}")
    print(f"Lead Email: {tag_result.get('lead_email')}")
    print(f"Tag Applied: {tag_result.get('tag_applied')}")
    print(f"Reason: {tag_result.get('reason')}")
    print(f"Status: {tag_result.get('status_message')}\n")

    # Verify in Mock CRM
    updated_crm_lead = mock_crm.get_lead(unqualified_lead_example['email'])
    if updated_crm_lead:
        print(f"--- Updated CRM Lead for {unqualified_lead_example['email']} ---")
        print(f"Status: {updated_crm_lead.get('status')}")
        print(f"Notes: {updated_crm_lead.get('notes')}")
        print(f"Details: {updated_crm_lead.get('qualification_summary')}")

    # Example for a lead that is qualified but we still want to tag (hypothetical)
    mock_crm.create_lead(qualified_lead_example)
    hypothetical_qual_result = {'qualified': True, 'summary': 'All good!'}
    tag_action_qualified = TagLeadInCRMAction(crm_handler=mock_crm)
    tag_result_qualified = tag_action_qualified.execute(qualified_lead_example, hypothetical_qual_result)
    print("\n--- Tag Lead In CRM Action Result (Hypothetical Qualified) ---")
    print(tag_result_qualified)

    lead_no_email = {'name': 'No Email User'}
    tag_result_no_email = tag_action.execute(lead_no_email, {'qualified': False, 'summary': 'No email'})
    print("\n--- Tag Lead In CRM Action Result (No Email) ---")
    print(tag_result_no_email)
