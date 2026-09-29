"""Simple Data Analyst Agent: fetches platform data and asks Gemini to explain it."""

from google import genai

from config import GEMINI_API_KEY
from db import (
    get_course_completion_summary,
    get_engagement_metrics,
    get_funnel_breakdown,
    get_most_popular_courses,
    get_overall_metrics,
    get_revenue_by_plan,
    get_revenue_metrics,
    get_review_metrics,
    get_users_by_country,
    get_users_by_persona,
    get_users_by_plan,
)

_client = genai.Client(api_key=GEMINI_API_KEY)
_MODEL = "gemini-3.5-flash-lite"


def build_data_context() -> str:
    """Small, cheap summary of every domain the dashboard covers, for the LLM prompt."""
    completion = get_course_completion_summary()
    overall = get_overall_metrics()
    engagement = get_engagement_metrics()
    revenue = get_revenue_metrics()
    reviews = get_review_metrics()

    parts = [
        f"Overall: {overall['total_enrollments']} enrollments, "
        f"{overall['completed']} completed, {overall['avg_progress']}% avg progress.",
        f"Engagement: {engagement['avg_minutes_per_week']} avg minutes/week, "
        f"{engagement['avg_quiz_score']}% avg quiz score.",
        f"Revenue: ${revenue['total_revenue']:,.0f} total, {revenue['refund_rate_pct']}% refund rate.",
        f"Reviews: {reviews['avg_stars']} avg stars over {reviews['total_reviews']} reviews.",
        "\nMost popular courses by number of enrollments (what people sign up/'buy' most):\n"
        + get_most_popular_courses().to_string(index=False),
        "\nEnrollment funnel:\n" + get_funnel_breakdown().to_string(index=False),
        "\nRevenue by subscription plan:\n" + get_revenue_by_plan().to_string(index=False),
        "\nUsers by subscription plan:\n" + get_users_by_plan().to_string(index=False),
        "\nUsers by persona:\n" + get_users_by_persona().to_string(index=False),
        "\nTop countries by number of users:\n" + get_users_by_country().to_string(index=False),
        "\nCourses with HIGHEST completion rate:\n" + completion.head(10).to_string(index=False),
        "\nCourses with LOWEST completion rate:\n" + completion.tail(10).to_string(index=False),
    ]
    return "\n".join(parts)


def answer_question(question: str) -> str:
    """Fetch a cross-domain data summary, then let Gemini answer the user's question about it."""
    data_context = build_data_context()

    prompt = f"""You are a senior data analyst for an online course platform, answering a
stakeholder's question in a live dashboard. Answer in the same language as the question.

Use ONLY the data below. The data has two separate "what do people buy" angles - don't
mix them up:
- COURSES: people "buy"/enroll in courses. Use "Most popular courses by number of
  enrollments" for "what do people buy/take most" questions about courses.
- SUBSCRIPTION PLANS: people pay for monthly/annual access. Use "Revenue by plan" /
  "Users by plan" only for questions specifically about plans, pricing or payment revenue.

If the question is ambiguous between these two angles, address the most likely one first
(usually courses), then briefly note the other angle too so nothing useful is missed.

Be specific and analytical, not just a restatement of a table: name concrete items,
cite numbers, and add one short insight (e.g. why this matters or what stands out).
Keep it to 3-5 sentences or a short bullet list. If the data truly doesn't cover the
question, say so plainly.

DATA:
{data_context}

QUESTION: {question}
"""

    response = _client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text


def generate_executive_summary() -> str:
    """Ask Gemini for a short exec-style narrative summary of the whole platform."""
    data_context = build_data_context()

    prompt = f"""You are a data analyst presenting a short executive summary of an online
course platform's current state to a business stakeholder.

Use ONLY the data below. Write 4-6 concise bullet points in Ukrainian, covering:
overall health, engagement, revenue, and one notable risk or opportunity.
Use markdown bullets. Cite concrete numbers. No preamble, no closing remarks.

DATA:
{data_context}
"""

    response = _client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text
