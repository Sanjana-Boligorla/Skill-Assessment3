from utils.llm_client import get_client


SYSTEM_PROMPT = """You are a Customer Feedback Analysis Agent specializing in product sentiment analysis,
customer experience evaluation, and identifying patterns in customer reviews and ratings.

Your role is to:
- Analyze customer reviews and ratings from the provided data
- Identify sentiment trends (positive, negative, neutral) per product and region
- Highlight common pain points and praise themes
- Evaluate return rates as a quality signal
- Identify products with high customer satisfaction vs dissatisfaction
- Extract actionable customer insights

Be specific with data. Reference actual product names, ratings, and review quotes from the data.
Structure your output clearly with sections for: Sentiment Overview, Product-Level Analysis,
Key Pain Points, Positive Highlights, and Actionable Customer Insights."""


def run(state: dict) -> dict:
    client = get_client()
    context = state.get("data_context", "")

    if not context:
        return {**state, "customer_insights": "No data available for customer feedback analysis."}

    prompt = f"""Analyze the following business data and generate a comprehensive Customer Insights Report.

DATA:
{context}

Generate a detailed Customer Insights Report covering:
1. Overall Sentiment Overview (with percentages/counts where possible)
2. Product-by-Product Sentiment Analysis (mention actual ratings and reviews)
3. Regional Customer Satisfaction Patterns
4. Top Customer Pain Points (backed by review evidence)
5. Customer Praise Highlights (what customers love)
6. Return Rate Analysis (which products have high returns and what it signals)
7. New Customer Acquisition Insights
8. Actionable Recommendations for Customer Experience Improvement

Be analytical and specific. Use actual numbers from the data."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=500,
    )

    insights = response.choices[0].message.content
    return {**state, "customer_insights": insights}
