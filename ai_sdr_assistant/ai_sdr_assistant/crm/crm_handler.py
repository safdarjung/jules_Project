from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

class CRMHandlerBase(ABC):
    """
    Base class for CRM interactions.
    """
    @abstractmethod
    def update_lead_status(self, lead_email: str, status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Updates the status of a lead in the CRM.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def add_note_to_lead(self, lead_email: str, note: str) -> bool:
        """
        Adds a note to a lead in the CRM.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_lead(self, lead_email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a lead from the CRM by email.
        Returns lead data as a dictionary or None if not found.
        """
        pass

    @abstractmethod
    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates a new lead in the CRM.
        Returns the ID of the new lead or None if creation failed.
        """
        pass


class MockCRMHandler(CRMHandlerBase):
    """
    Mock CRM handler that prints actions to the console.
    Simulates CRM interactions for testing and development.
    """
    def __init__(self):
        self.leads: Dict[str, Dict[str, Any]] = {} # In-memory store for leads
        print("MockCRMHandler initialized.")

    def update_lead_status(self, lead_email: str, status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        if lead_email in self.leads:
            self.leads[lead_email]['status'] = status
            if details:
                self.leads[lead_email].update(details)
            print(f"CRM_MOCK: Lead '{lead_email}' status updated to '{status}'. Details: {details or {}}")
            return True
        print(f"CRM_MOCK_WARN: Lead '{lead_email}' not found. Cannot update status.")
        return False

    def add_note_to_lead(self, lead_email: str, note: str) -> bool:
        if lead_email in self.leads:
            if 'notes' not in self.leads[lead_email]:
                self.leads[lead_email]['notes'] = []
            self.leads[lead_email]['notes'].append(note)
            print(f"CRM_MOCK: Note added to lead '{lead_email}': '{note}'")
            return True
        print(f"CRM_MOCK_WARN: Lead '{lead_email}' not found. Cannot add note.")
        return False

    def get_lead(self, lead_email: str) -> Optional[Dict[str, Any]]:
        lead = self.leads.get(lead_email)
        if lead:
            print(f"CRM_MOCK: Lead '{lead_email}' retrieved: {lead}")
        else:
            print(f"CRM_MOCK_INFO: Lead '{lead_email}' not found.")
        return lead

    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[str]:
        email = lead_data.get('email')
        if not email:
            print("CRM_MOCK_ERROR: Email is required to create a lead.")
            return None
        if email in self.leads:
            print(f"CRM_MOCK_INFO: Lead '{email}' already exists. Updating.")
            self.leads[email].update(lead_data)
        else:
            self.leads[email] = lead_data
            print(f"CRM_MOCK: Lead '{email}' created: {lead_data}")

        # Simulate a CRM ID, could be email itself or a generated ID
        lead_id = email
        self.leads[email]['id'] = lead_id
        return lead_id

# Example usage (can be removed or kept for testing)
if __name__ == '__main__':
    mock_crm = MockCRMHandler()
    mock_crm.create_lead({'email': 'test@example.com', 'name': 'Test User', 'company_name': 'Example Corp'})
    mock_crm.update_lead_status('test@example.com', 'Contacted', {'last_contact_method': 'Email'})
    mock_crm.add_note_to_lead('test@example.com', 'Sent initial outreach email.')
    retrieved_lead = mock_crm.get_lead('test@example.com')
    non_existent_lead = mock_crm.get_lead('noone@example.com')
