import json
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def scrape_website(url: str, max_chars: int = 5000) -> str:
    if not url:
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "meta", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse whitespace
        import re
        text = re.sub(r"\s{2,}", " ", text)
        return text[:max_chars]
    except Exception:
        return ""


def research_lead(lead: dict) -> dict:
    """
    Scrapes the org's website and uses GPT-4o to extract actionable intel:
    decision maker names, upcoming events, catering angles, personalization hooks.
    """
    website_content = scrape_website(lead.get("website", ""))

    prompt = f"""You are a sales intelligence analyst doing pre-call research for a Chick-fil-A Catering operator.

The rep is about to reach out to this organization to offer Chick-fil-A Catering services for their events.

ORGANIZATION:
- Name: {lead['organization_name']}
- Category: {lead['category']}
- Address: {lead.get('address', '')}
- Phone: {lead.get('phone', '')}
- Website: {lead.get('website', '')}
- Decision Maker Role: {lead['likely_decision_maker_role']}
- Seasonal Opportunity: {lead['seasonal_opportunity']}
- Google Rating: {lead.get('rating', '')} ({lead.get('ratings_count', 0)} reviews)

WEBSITE CONTENT SCRAPED:
{website_content if website_content else "Website not available or could not be scraped."}

Your job: extract everything useful for a sales rep. Be specific. If you find real names, use them. If you find real event dates, use them. If you cannot find specific info, make a sharp, well-reasoned inference based on the org type, location, and time of year — and mark it (estimated).

Return ONLY valid JSON with these exact keys:
{{
  "decision_maker_name": "The most likely specific person's name and title to contact. Use real name if found on site, otherwise best inference like 'Principal [Last Name]' or 'Dr. [Last Name]'",
  "decision_maker_email": "Email if found on site, otherwise empty string",
  "upcoming_events": [
    {{"event": "event name", "date": "date or timeframe", "catering_fit": "how CFA catering fits this event"}}
  ],
  "catering_angle": "The single strongest, most specific reason to reach out right now — tied to a real event, timing, or need. 1-2 sentences.",
  "org_notes": ["3 specific things a rep must know about this org before calling or emailing"],
  "personalization_hook": "One genuine, specific opening observation about this org — something a real person would notice. NOT generic. This goes at the start of the email or call.",
  "best_contact_timing": "Best time of year / week to reach this type of decision maker and why"
}}

No markdown. No explanation. Just the JSON."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {}
