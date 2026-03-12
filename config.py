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

DECISION_MAKER_ROLES = {
    "school": "Principal / Director of Operations",
    "hospital": "Director of Food Services / Facilities Manager",
    "church": "Church Administrator / Events Coordinator",
    "corporate office": "Director of Workplace Services / Facilities Manager",
}
