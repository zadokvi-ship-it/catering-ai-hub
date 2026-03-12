SHEET_ID = "1jiAxJaFTiWcrony7g8--x1-cby2k-CE_zkOe3MxlNUA"

LEADS_SHEET = "Leads"
EMAIL_QUEUE_SHEET = "EmailQueue"

PIPELINE_STATUSES = [
    "Not Contacted",
    "Contacted",
    "Meeting Scheduled",
    "Proposal Sent",
    "Closed Won",
    "Closed Lost",
]

LEAD_COLUMNS = [
    "organization_name",
    "category",
    "address",
    "phone",
    "website",
    "estimated_size",
    "rating",
    "ratings_count",
    "place_id",
    "likely_decision_maker_role",
    "seasonal_opportunity",
    "priority_score",
    "status",
    "assigned_to",
    "last_contact_date",
    "next_follow_up_date",
    "actual_revenue",
    "notes",
]

EMAIL_QUEUE_COLUMNS = [
    "place_id",
    "organization_name",
    "to_name",
    "to_email",
    "subject",
    "body",
    "status",
    "drafted_at",
    "reviewed_by",
    "reviewed_at",
    "notes",
]

CATEGORY_OPTIONS = ["school", "hospital", "church", "corporate office"]

SETTINGS_SHEET = "Settings"
TEAM_MEMBERS_SHEET = "TeamMembers"

DEFAULT_SETTINGS = {
    "default_zip": "",
    "default_radius": "10",
    "default_category": "school",
    "pipeline_small": "500",
    "pipeline_medium": "1000",
    "pipeline_large": "2000",
    "theme": "dark",
    "brand_voice": "",
    "sample_email_1": "",
    "sample_email_2": "",
    "sample_email_3": "",
    "company_name": "Chick-fil-A Catering",
    "company_location": "",
    "rep_name": "",
    "rep_title": "Catering Specialist",
    "rep_email": "",
    "rep_phone": "",
}

DECISION_MAKER_ROLES = {
    "school": "Principal / Director of Operations",
    "hospital": "Director of Food Services / Facilities Manager",
    "church": "Church Administrator / Events Coordinator",
    "corporate office": "Director of Workplace Services / Facilities Manager",
}
