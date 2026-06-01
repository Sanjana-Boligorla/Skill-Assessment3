from utils.llm_client import get_client


SYSTEM_PROMPT = """You are a Market Research Agent with expertise in product market analysis,
competitive landscape evaluation, and identifying market trends and opportunities.

Your role is to:
- Analyze product performance data to infer market positioning
- Identify market trends from sales patterns and customer behavior
- Evaluate category-level performance and market share signals
- Assess pricing and revenue patterns to understand market dynamics
- Identify growth opportunities and underperforming segments
- Provide market-level strategic context

Use the sales and product data as market signals. Reference actual categories, regions, and products."""


def run(state: dict) -> dict:
    client = get_client()
    context = state.get("data_context", "")
    customer_insights = state.get("customer_insights", "")

    if not context:
        return {**state, "market_research": "No data available for market research analysis."}

    prompt = f"""Analyze the following business data and generate a comprehensive Market Research Summary.

BUSINESS DATA:
{context}

CUSTOMER INSIGHTS (from previous analysis):
{customer_insights[:500] if customer_insights else 'Not yet available'}

Generate a detailed Market Research Summary covering:
1. Market Overview & Current Position
   - Revenue and growth patterns by category and region
   - Market share distribution across product lines
2. Category Performance Analysis
   - Which categories (Electronics, Wearables, Accessories, Audio, Smart Home) are growing vs declining
   - Revenue velocity and profit margin comparison
3. Regional Market Analysis
   - Geographic performance breakdown
   - Regional growth opportunities and underserved markets
4. Pricing & Revenue Dynamics
   - Revenue per unit analysis
   - Marketing ROI assessment (marketing spend vs revenue)
5. Competitive Positioning Signals
   - Based on product ratings, returns, and customer feedback, how products are positioned
6. Market Trend Identification
   - Emerging demand signals from sales patterns
7. Market Opportunities & Risks

Be specific with numbers and percentages from the data provided."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=500,
    )

    research = response.choices[0].message.content
    return {**state, "market_research": research}
