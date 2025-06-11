from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LeadQualifierBase(ABC):
    """
    Base class for lead qualification.
    """
    @abstractmethod
    def qualify(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to qualify a lead.
        Takes an enriched lead dictionary and returns a dictionary
        containing the qualification status and potentially a score or reasons.
        """
        pass

class ICPQualifier(LeadQualifierBase):
    """
    Qualifies leads based on Ideal Customer Profile (ICP) criteria.
    """
    def __init__(self, icp_criteria: Dict[str, Any]):
        self.icp_criteria = icp_criteria

    def _parse_size(self, size_str: Optional[str]) -> Optional[int]:
        """
        Parses a size string (e.g., '50-200 employees') to get the minimum number of employees.
        Returns None if parsing fails or size_str is None.
        """
        if not size_str:
            return None
        try:
            # Simplistic parsing, assumes format like "X-Y employees" or "X+ employees" or "X employees"
            if '-' in size_str:
                return int(size_str.split('-')[0])
            elif '+' in size_str:
                return int(size_str.replace('+', '').split(' ')[0])
            else: # "X employees"
                return int(size_str.split(' ')[0])
        except (ValueError, IndexError):
            return None # Cannot parse

    def qualify(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualifies a lead against the ICP criteria.
        """
        reasons: Dict[str, bool] = {}
        overall_qualified = True

        # Check industry
        required_industry = self.icp_criteria.get('industry')
        lead_industry = lead.get('industry')
        if required_industry:
            if lead_industry and required_industry.lower() == lead_industry.lower():
                reasons['industry_match'] = True
            else:
                reasons['industry_match'] = False
                overall_qualified = False

        # Check company size (min_employees)
        required_min_employees = self.icp_criteria.get('min_employees')
        lead_size_str = lead.get('size') # e.g., "50-200 employees"

        if required_min_employees is not None:
            lead_min_employees = self._parse_size(lead_size_str)
            if lead_min_employees is not None and lead_min_employees >= required_min_employees:
                reasons['size_match'] = True
            else:
                reasons['size_match'] = False
                overall_qualified = False
                if lead_min_employees is None and lead_size_str:
                    reasons['size_parse_error'] = f"Could not parse size: {lead_size_str}"


        # Future criteria checks can be added here (e.g., country, relevant_news)

        qualification_result: Dict[str, Any] = {
            'qualified': overall_qualified,
            'reasons': reasons,
            'icp_criteria_used': self.icp_criteria # For transparency
        }

        if not overall_qualified:
            failure_summary = []
            if reasons.get('industry_match') == False:
                failure_summary.append(f"Industry '{lead_industry}' does not match required '{required_industry}'.")
            if reasons.get('size_match') == False:
                parsed_size = self._parse_size(lead_size_str)
                if parsed_size is not None:
                    failure_summary.append(f"Company size '{parsed_size}' (from '{lead_size_str}') does not meet minimum of '{required_min_employees}'.")
                elif lead_size_str: # Size string exists but couldn't be parsed
                     failure_summary.append(f"Company size '{lead_size_str}' could not be parsed or does not meet minimum of '{required_min_employees}'.")
                else: # No size info provided in lead
                    failure_summary.append(f"Company size information missing, cannot meet minimum of '{required_min_employees}'.")
            qualification_result['summary'] = " ".join(failure_summary) if failure_summary else "General criteria not met."
        else:
            qualification_result['summary'] = "Lead matches all ICP criteria."

        return qualification_result
