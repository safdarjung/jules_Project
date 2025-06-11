from typing import Dict, Any, List

# Ideal Customer Profile (ICP) criteria
IDEAL_CUSTOMER_PROFILE: Dict[str, Any] = {
    'industry': 'Software',
    'min_employees': 50,
    # Future criteria:
    # 'country': 'USA',
    # 'has_relevant_news': True, # e.g., recent funding, new product launch
    # 'technologies_used': ['Salesforce', 'HubSpot'],
}

# User Profile - Defines the user of this SDR assistant
USER_PROFILE: Dict[str, Any] = {
    'my_company_name': "My Awesome Consulting Inc.",
    'services_offered': "AI strategy, custom machine learning model development, data analytics solutions.",
    'target_keywords': ["enterprise software", "SaaS solutions", "data analytics", "AI adoption"], # For searching news/prospects
    'target_industry': ["Technology", "Healthcare", "Finance"], # List of primary target industries
    'target_company_size': ["50-200 employees", "200-1000 employees"], # List of target company size brackets
    'target_location': "San Francisco Bay Area", # Can be a string or a more structured dict like {'city': 'San Francisco', 'region': 'CA', 'country': 'USA'}
    'sdr_name': "Alex the AI SDR", # Name to use in email signatures
    'sdr_email': "alex.aisdr@example.com" # SDR's email for contact
}


# API Keys (placeholders - replace with actual keys or use environment variables)
SOME_API_KEY: str = "YOUR_API_KEY_HERE" # Example: OpenAI API Key
ANOTHER_API_KEY: str = "ANOTHER_KEY_HERE" # Example: NewsAPI Key or Clearbit Key

# Other configurations
DEFAULT_EMAIL_SUBJECT: str = "Following Up"
CRM_API_ENDPOINT: str = "https://api.examplecrm.com/v1"

# Logging Configuration
LOG_LEVEL: str = "INFO" # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE: str = "ai_sdr_assistant.log" # Path to the log file, if file logging is desired
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Email sending configuration (placeholders)
SMTP_SERVER: str = "smtp.example.com"
SMTP_PORT: int = 587
SMTP_USERNAME: str = "your_email@example.com"
SMTP_PASSWORD: str = "your_email_password" # Consider using environment variables for this
EMAIL_SENDER_NAME: str = USER_PROFILE.get('sdr_name', "AI SDR")
EMAIL_SENDER_ADDRESS: str = USER_PROFILE.get('sdr_email', "noreply@example.com")
