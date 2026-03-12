import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def _brand_voice_block(brand_voice: str, sample_emails: list[str]) -> str:
    """Build the style/voice injection block for prompts."""
    block = ""
    if brand_voice and brand_voice.strip():
        block += f"\n\nBRAND VOICE & TONE:\n{brand_voice.strip()}\n"
    if sample_emails:
        valid = [e.strip() for e in sample_emails if e and e.strip()]
        if valid:
            block += "\n\nREAL EMAIL EXAMPLES FROM OUR TEAM (match this style exactly):\n"
            for i, email in enumerate(valid, 1):
                block += f"\n--- Example {i} ---\n{email}\n"
    return block


def generate_email_draft(lead: dict, brand_voice: str = "", sample_emails: list = None) -> dict:
    sample_emails = sample_emails or []
    voice_block = _brand_voice_block(brand_voice, sample_emails)

    has_examples = bool([e for e in sample_emails if e and e.strip()])

    style_instructions = """
STRICT STYLE RULES — follow every one of these:
- Write like a real person, not a salesperson. Conversational, direct, confident.
- Keep the email SHORT. Max 5-7 sentences total. Busy people don't read long emails.
- NO generic openers. Never use: "I hope this email finds you well", "My name is", "I wanted to reach out", "I am writing to".
- Lead with a specific, relevant observation about their organization or the opportunity — not about yourself.
- ONE clear ask at the end. Not two. Not three. One.
- NO bullet points or lists in the email body. Write in sentences.
- Subject line: lowercase, casual, specific. NOT a marketing headline.
- Sound like a text message from a professional, not a press release.
- Use [First Name] and [Your Name] as placeholders.
- Do not mention your company name — leave a placeholder [Company] only if naturally needed.
""" if not has_examples else """
STYLE RULES:
- Match the tone, length, and structure of the example emails provided above EXACTLY.
- Use [First Name] and [Your Name] as placeholders.
- Keep it as natural and human as the examples.
- ONE clear ask at the end.
"""

    prompt = f"""You are writing a cold outreach email for a catering company targeting a new business lead.
{voice_block}
{style_instructions}

LEAD DETAILS:
- Organization: {lead['organization_name']}
- Category: {lead['category']}
- Address: {lead.get('address', 'N/A')}
- Decision Maker Role: {lead['likely_decision_maker_role']}
- Seasonal Opportunity: {lead['seasonal_opportunity']}
- Estimated Size: {lead['estimated_size']}
- Google Rating: {lead.get('rating', 'N/A')} ({lead.get('ratings_count', 0)} reviews)

Return ONLY valid JSON with these exact keys:
- subject: email subject line (lowercase, casual, specific)
- body: full email body

No markdown. No explanation. Just the JSON."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def generate_phone_script(lead: dict, brand_voice: str = "") -> str:
    voice_block = f"\n\nBRAND VOICE:\n{brand_voice.strip()}\n" if brand_voice and brand_voice.strip() else ""

    prompt = f"""You are a B2B catering sales coach writing a cold call phone script.
{voice_block}

LEAD:
- Organization: {lead['organization_name']}
- Category: {lead['category']}
- Decision Maker Role: {lead['likely_decision_maker_role']}
- Seasonal Opportunity: {lead['seasonal_opportunity']}
- Estimated Size: {lead['estimated_size']}
- Address: {lead.get('address', 'N/A')}

Write a realistic, natural-sounding cold call script. Structure it exactly like this:

**BEFORE YOU DIAL**
(3 bullet points — quick things to know/research before calling)

**OPENER** (first 10 seconds)
(The exact words to say. Confident, not robotic. Get to the point fast. Do NOT say "How are you today?")

**BRIDGE** (if they stay on)
(1-2 sentences connecting their situation to why you're calling)

**3 QUALIFYING QUESTIONS**
(Questions that uncover budget, decision process, current vendor, timing — numbered)

**YOUR VALUE IN ONE SENTENCE**
(A single, specific, jargon-free sentence about what you do for organizations like theirs)

**HANDLING THE TOP 3 OBJECTIONS**
For each objection: state it, then give the exact response to say out loud. Keep responses short and natural.
1. "We already have someone."
2. "We're not interested / not the right time."
3. "Send me an email." (the brush-off)

**THE ASK** (close of the call)
(Exact words for requesting the next step — a meeting, a callback, a site visit. Offer two specific time options.)

**VOICEMAIL SCRIPT** (if no answer)
(15-20 second voicemail. Specific, intriguing, not salesy. Leave them wanting to call back.)

Keep all language natural, like a real person talking — not a script being read."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def generate_prep_brief(lead: dict, brand_voice: str = "", sample_emails: list = None) -> str:
    sample_emails = sample_emails or []
    voice_block = _brand_voice_block(brand_voice, sample_emails)

    prompt = f"""You are a B2B catering sales strategist preparing a rep for an outreach call.
{voice_block}

LEAD:
- Organization: {lead['organization_name']}
- Category: {lead['category']}
- Address: {lead.get('address', 'N/A')}
- Phone: {lead.get('phone', 'N/A')}
- Website: {lead.get('website', 'N/A')}
- Estimated Size: {lead['estimated_size']}
- Google Rating: {lead.get('rating', 'N/A')} ({lead.get('ratings_count', 0)} reviews)
- Decision Maker: {lead['likely_decision_maker_role']}
- Seasonal Opportunity: {lead['seasonal_opportunity']}
- Priority Score: {lead['priority_score']}

Provide these four sections. Be specific to this organization. No generic filler.

1. INTEL BRIEF (3-4 bullets — what to know about this org before reaching out)
2. ONE-LINE VALUE PROP (a single sentence tailored to their category and situation)
3. TOP 4 OBJECTIONS & EXACT RESPONSES (what they'll say and what you say back — keep it natural)
4. FOLLOW-UP SEQUENCE (Day 0 through close — specific actions, specific timing)"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content
