from abc import ABC, abstractmethod
from typing import List, Dict

class LeadIngestorBase(ABC):
    """
    Base class for lead ingestion.
    """
    @abstractmethod
    def ingest(self) -> List[Dict[str, str]]:
        """
        Abstract method to ingest leads.
        Should be implemented by subclasses.
        Returns a list of lead objects (dictionaries).
        """
        pass

class WebsiteFormIngestor(LeadIngestorBase):
    """
    Placeholder for ingesting leads from a website form.
    """
    def ingest(self) -> List[Dict[str, str]]:
        """
        Ingests leads from a website form.
        Currently returns a hardcoded list of sample leads.
        """
        # Placeholder for actual website form integration
        sample_leads: List[Dict[str, str]] = [
            {'email': 'test1@example.com', 'name': 'Test User One'},
            {'email': 'test2@example.com', 'name': 'Test User Two'},
        ]
        return sample_leads
