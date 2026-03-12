import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def generate_prep_brief(lead: dict) -> str:
    prompt = f"""
You are a professional B2B catering sales strategist.

Prepare a structured outreach strategy for the following institution:

Organization: {lead['organization_name']}
Category: {lead['category']}
Address: {lead.get('address', 'N/A')}
Estimated Size: {lead['estimated_size']}
Google Rating: {lead.get('rating', 'N/A')} ({lead.get('ratings_count', 0)} reviews)
Decision Maker: {lead['likely_decision_maker_role']}
Seasonal Opportunity: {lead['seasonal_opportunity']}
Priority Score: {lead['priority_score']}

Provide these sections:

1. 60-Second Pre-Call Strategy
2. Tailored Outreach Email (subject + body, leave [brackets] for personalization)
3. Likely Objections & Responses (top 4)
4. Recommended Follow-Up Timeline

Be concise, tactical, and specific to this organization. No fluff.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def generate_email_draft(lead: dict) -> dict:
    prompt = f"""
You are a B2B catering sales expert.

Write a cold outreach email for this lead:

Organization: {lead['organization_name']}
Category: {lead['category']}
Address: {lead.get('address', 'N/A')}
Decision Maker Role: {lead['likely_decision_maker_role']}
Seasonal Opportunity: {lead['seasonal_opportunity']}
Estimated Size: {lead['estimated_size']}

Return ONLY valid JSON with these exact keys:
- subject: email subject line
- body: full email body (use [First Name] and [Your Name] as placeholders)

No markdown. No explanation. Just the JSON.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    import json
    return json.loads(response.choices[0].message.content)
