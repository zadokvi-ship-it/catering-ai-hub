import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def _voice_block(brand_voice: str, sample_emails: list) -> str:
    block = ""
    if brand_voice and brand_voice.strip():
        block += f"\n\nBRAND VOICE:\n{brand_voice.strip()}\n"
    valid_samples = [e.strip() for e in (sample_emails or []) if e and e.strip()]
    if valid_samples:
        block += "\n\nREAL EMAIL EXAMPLES — MATCH THIS STYLE EXACTLY:\n"
        for i, email in enumerate(valid_samples, 1):
            block += f"\n--- Example {i} ---\n{email}\n"
    return block


def _research_block(research: dict) -> str:
    if not research:
        return ""
    block = "\n\nRESEARCH INTEL:\n"
    if research.get("decision_maker_name"):
        block += f"- Decision Maker: {research['decision_maker_name']}\n"
    if research.get("decision_maker_email"):
        block += f"- Email: {research['decision_maker_email']}\n"
    if research.get("upcoming_events"):
        block += "- Upcoming Events:\n"
        for ev in research["upcoming_events"]:
            block += f"  • {ev.get('event','')} ({ev.get('date','')}) — {ev.get('catering_fit','')}\n"
    if research.get("catering_angle"):
        block += f"- Best Catering Angle: {research['catering_angle']}\n"
    if research.get("personalization_hook"):
        block += f"- Personalization Hook: {research['personalization_hook']}\n"
    if research.get("org_notes"):
        block += "- Key Org Notes:\n"
        for note in research["org_notes"]:
            block += f"  • {note}\n"
    return block


def generate_full_email(lead: dict, research: dict = None, brand_voice: str = "",
                        sample_emails: list = None, rep_settings: dict = None) -> dict:
    research = research or {}
    rep_settings = rep_settings or {}
    voice_block = _voice_block(brand_voice, sample_emails)
    research_block = _research_block(research)
    has_samples = bool([e for e in (sample_emails or []) if e and e.strip()])

    rep_name = rep_settings.get("rep_name", "[Your Name]")
    rep_title = rep_settings.get("rep_title", "Catering Specialist")
    rep_phone = rep_settings.get("rep_phone", "[Phone]")
    rep_email = rep_settings.get("rep_email", "[Email]")
    company_name = rep_settings.get("company_name", "Chick-fil-A Catering")
    company_location = rep_settings.get("company_location", "")

    decision_maker = research.get("decision_maker_name") or f"[{lead['likely_decision_maker_role']}]"
    to_email = research.get("decision_maker_email", "[email]")

    style_rules = """
STYLE RULES — non-negotiable:
- Professional but warm. Sound like a real person at Chick-fil-A — genuine, caring, not salesy.
- SHORT. 4-6 sentences max in the body. Busy decision makers don't read long emails.
- Open with the personalization hook or a specific relevant observation. Never with "My name is" or "I hope this email finds you well."
- Reference a SPECIFIC upcoming event or seasonal opportunity from the research — use real names and dates when available.
- One clear, easy ask at the end. Not multiple CTAs.
- No bullet points in the body.
- Subject line: specific, lowercase, conversational. Not a marketing headline.
- Signature should look professional and complete.
""" if not has_samples else """
STYLE RULES:
- Match the provided email examples exactly in tone and length.
- Professional but warm — Chick-fil-A brand voice: genuine, caring, quality-focused.
- Reference a SPECIFIC upcoming event or seasonal opportunity from the research.
- One clear ask at the end.
"""

    prompt = f"""You are writing a cold outreach email on behalf of {company_name}.
{voice_block}
{research_block}
{style_rules}

LEAD:
- Organization: {lead['organization_name']}
- Category: {lead['category']}
- Address: {lead.get('address', '')}
- Estimated Size: {lead['estimated_size']}
- Seasonal Opportunity: {lead['seasonal_opportunity']}

REP INFO:
- Name: {rep_name}
- Title: {rep_title}
- Phone: {rep_phone}
- Email: {rep_email}
- Company: {company_name}{f" | {company_location}" if company_location else ""}

Return ONLY valid JSON with these exact keys:
{{
  "to_name": "the decision maker's name (use research if available)",
  "to_email": "{to_email}",
  "subject": "email subject line",
  "body": "full email body — 4-6 sentences, no bullet points, ends with one clear ask",
  "signature": "full professional signature block",
  "full_email": "the complete ready-to-send email formatted as: Subject: ...\\n\\n[body]\\n\\n[signature]"
}}

No markdown. No explanation. Just the JSON."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def generate_phone_script(lead: dict, research: dict = None, brand_voice: str = "",
                          rep_settings: dict = None) -> str:
    research = research or {}
    rep_settings = rep_settings or {}
    voice_block = f"\n\nBRAND VOICE:\n{brand_voice.strip()}\n" if brand_voice and brand_voice.strip() else ""
    research_block = _research_block(research)

    company_name = rep_settings.get("company_name", "Chick-fil-A Catering")
    rep_name = rep_settings.get("rep_name", "[Your Name]")

    decision_maker = research.get("decision_maker_name") or f"the {lead['likely_decision_maker_role']}"
    upcoming = research.get("upcoming_events", [])
    event_ref = f"{upcoming[0]['event']} on {upcoming[0]['date']}" if upcoming else lead['seasonal_opportunity']

    prompt = f"""You are a Chick-fil-A Catering sales coach writing a cold call script for a rep.
{voice_block}
{research_block}

REP: {rep_name} from {company_name}
CALLING: {lead['organization_name']} — reaching {decision_maker}
BEST ANGLE: {research.get('catering_angle') or lead['seasonal_opportunity']}
KEY EVENT TO REFERENCE: {event_ref}

Write a realistic, natural phone script. The rep works for Chick-fil-A Catering — warm, genuine, "my pleasure" energy. Not pushy. Not robotic.

Structure it exactly like this:

---
**BEFORE YOU DIAL** (30 seconds of prep)
- What you know about this org
- The specific event/timing angle to lead with
- What you want to walk away with from this call

---
**OPENER** (first 10 seconds — the exact words)
(Get to the point immediately. Reference the specific event or timing. Do NOT say "How are you doing today?" — this kills credibility.)

---
**IF THEY STAY ON — THE BRIDGE**
(1-2 sentences. Why you're calling them specifically, right now.)

---
**3 QUALIFYING QUESTIONS**
(Uncover: who makes the decision, current food vendor, budget/timeline, upcoming events)
1.
2.
3.

---
**YOUR VALUE IN ONE SENTENCE**
(Specific to their category. Mention Chick-fil-A by name. What you make easier for them.)

---
**HANDLING OBJECTIONS** (exact words to say)

"We already have someone."
→

"Not interested / bad time."
→

"Just send me an email." (the brush-off)
→

---
**THE CLOSE**
(Exact words for the next-step ask. Offer two specific time options for a follow-up or site visit.)

---
**IF NO ANSWER — VOICEMAIL**
(15-20 seconds. Specific, genuine, curiosity-provoking. Reference the event. Leave your number twice.)

---

Keep ALL language natural. Write it how a real CFA rep would actually say it — not how a textbook says to say it."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def generate_prep_brief(lead: dict, research: dict = None, brand_voice: str = "",
                        sample_emails: list = None, rep_settings: dict = None) -> str:
    research = research or {}
    rep_settings = rep_settings or {}
    voice_block = _voice_block(brand_voice, sample_emails)
    research_block = _research_block(research)
    company_name = rep_settings.get("company_name", "Chick-fil-A Catering")

    prompt = f"""You are preparing a {company_name} sales rep for outreach to a new lead.
{voice_block}
{research_block}

LEAD:
- Organization: {lead['organization_name']}
- Category: {lead['category']}
- Address: {lead.get('address', '')}
- Phone: {lead.get('phone', '')}
- Website: {lead.get('website', '')}
- Estimated Size: {lead['estimated_size']}
- Google Rating: {lead.get('rating', '')} ({lead.get('ratings_count', 0)} reviews)
- Decision Maker: {lead['likely_decision_maker_role']}
- Seasonal Opportunity: {lead['seasonal_opportunity']}
- Priority Score: {lead['priority_score']}

Write four tight sections. Be specific to this exact organization. Use real names and events from the research where available.

**1. INTEL BRIEF**
4-5 bullet points. Things the rep must know before picking up the phone. Include specific people, events, dates, and context.

**2. WHY CHICK-FIL-A CATERING — RIGHT NOW**
2-3 sentences. The most compelling argument for reaching out to THIS organization at THIS moment. Tie it to a real event or timing.

**3. TOP OBJECTIONS & EXACT RESPONSES**
4 objections they'll hear. For each: what they'll say → what you say back. Keep it conversational.

**4. OUTREACH SEQUENCE**
Day-by-day action plan from first contact to close. Specific deliverables at each step (not generic "follow up")."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content
