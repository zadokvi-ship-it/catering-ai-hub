import os
import googlemaps
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from config import DECISION_MAKER_ROLES, LEAD_COLUMNS

load_dotenv()

PLACES_TYPE_MAP = {
    "school": {"type": "school", "keyword": "K-12 school"},
    "hospital": {"type": "hospital", "keyword": "hospital medical center"},
    "church": {"type": "church", "keyword": "church"},
    "corporate office": {"type": "establishment", "keyword": "corporate office headquarters"},
}


def get_gmaps_client():
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        raise ValueError("GOOGLE_PLACES_API_KEY not set in .env")
    return googlemaps.Client(key=key)


def get_lat_lng(gmaps, zip_code):
    result = gmaps.geocode(zip_code)
    if result:
        loc = result[0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    return None, None


def estimate_size(ratings_count):
    if ratings_count >= 500:
        return "large"
    elif ratings_count >= 100:
        return "medium"
    return "small"


def get_seasonal_opportunity(category):
    month = datetime.now().month
    if category == "school":
        if month in [8, 9]:
            return "Back-to-school season — high event volume starting now"
        if month in [11, 12]:
            return "Holiday events and year-end celebrations"
        if month in [5, 6]:
            return "Graduation and end-of-year events upcoming"
        return "Spring semester — ongoing recurring event opportunities"
    elif category == "hospital":
        return "Year-round — staff appreciation, patient family events, recurring"
    elif category == "church":
        if month in [11, 12]:
            return "Holiday season — Christmas events and year-end gatherings"
        if month in [3, 4]:
            return "Easter season — high attendance events upcoming"
        return "Year-round — Sunday events and community gatherings, recurring"
    elif category == "corporate office":
        if month in [11, 12]:
            return "Q4 budget spend — holiday parties and year-end events"
        if month in [1, 2]:
            return "New year kickoff events and Q1 planning"
        if month in [6, 7, 8]:
            return "Summer onboarding and intern programs"
        return "Ongoing — quarterly business events, recurring"
    return "Year-round opportunity, recurring"


def calculate_priority(row):
    score = 0

    size = str(row.get("estimated_size", "")).lower()
    if size == "large":
        score += 30
    elif size == "medium":
        score += 20
    elif size == "small":
        score += 10

    category = str(row.get("category", "")).lower()
    if "school" in category:
        score += 20
    elif "hospital" in category:
        score += 18
    elif "corporate" in category:
        score += 17
    elif "church" in category:
        score += 15

    role = str(row.get("likely_decision_maker_role", "")).lower()
    if any(x in role for x in ["principal", "director", "executive", "head"]):
        score += 15
    elif any(x in role for x in ["manager", "administrator"]):
        score += 10
    else:
        score += 5

    opportunity = str(row.get("seasonal_opportunity", "")).lower()
    if any(x in opportunity for x in ["now", "starting now", "upcoming"]):
        score += 25
    elif any(x in opportunity for x in ["fall", "spring", "summer", "q4", "q1", "season"]):
        score += 15
    else:
        score += 10

    if any(x in opportunity for x in ["year-round", "recurring", "ongoing", "annual"]):
        score += 10
    else:
        score += 5

    return score


def generate_leads(zip_code: str, category: str, radius_miles: int = 10) -> pd.DataFrame:
    gmaps = get_gmaps_client()

    lat, lng = get_lat_lng(gmaps, zip_code)
    if lat is None:
        raise ValueError(f"Could not geocode ZIP code: {zip_code}")

    config = PLACES_TYPE_MAP.get(category, {"type": "establishment", "keyword": category})
    radius_meters = int(radius_miles * 1609.34)

    results = gmaps.places_nearby(
        location=(lat, lng),
        radius=radius_meters,
        type=config["type"],
        keyword=config["keyword"],
    )

    places = results.get("results", [])

    leads = []
    for place in places[:15]:
        if place.get("business_status") != "OPERATIONAL":
            continue

        ratings_count = place.get("user_ratings_total", 0)
        size = estimate_size(ratings_count)
        seasonal = get_seasonal_opportunity(category)

        # Enrich with phone + website from Places Details API
        phone, website = "", ""
        try:
            details = gmaps.place(
                place.get("place_id"),
                fields=["formatted_phone_number", "website"],
            )
            result = details.get("result", {})
            phone = result.get("formatted_phone_number", "")
            website = result.get("website", "")
        except Exception:
            pass

        lead = {
            "organization_name": place.get("name", ""),
            "category": category,
            "address": place.get("vicinity", ""),
            "phone": phone,
            "website": website,
            "estimated_size": size,
            "rating": place.get("rating", 0),
            "ratings_count": ratings_count,
            "place_id": place.get("place_id", ""),
            "likely_decision_maker_role": DECISION_MAKER_ROLES.get(category, "Operations Manager"),
            "seasonal_opportunity": seasonal,
            "priority_score": 0,
            "status": "Not Contacted",
            "assigned_to": "",
            "last_contact_date": "",
            "next_follow_up_date": "",
            "actual_revenue": 0,
            "notes": "",
        }
        leads.append(lead)

    if not leads:
        return pd.DataFrame(columns=LEAD_COLUMNS)

    df = pd.DataFrame(leads)
    df["priority_score"] = df.apply(calculate_priority, axis=1)
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    return df[LEAD_COLUMNS]
