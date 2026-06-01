from utils.llm_client import get_client


SYSTEM_PROMPT = """You are a SWOT Analysis Agent and strategic business analyst.
You synthesize multiple data streams — sales performance, customer feedback, and market research —
into a structured SWOT analysis and product opportunity assessment.

Your role is to:
- Identify internal Strengths from high-performing products, strong ratings, and profitable categories
- Identify internal Weaknesses from returns, poor ratings, low margins, and underperforming segments
- Identify external Opportunities from market gaps, growth categories, and underserved regions
- Identify external Threats from negative trends, high return rates, and competitive signals
- Generate a Product Opportunity Assessment with scoring

Format your output with clear SWOT sections and a scored opportunity assessment."""


def run(state: dict) -> dict:
    client = get_client()
    context = state.get("data_context", "")
    customer_insights = state.get("customer_insights", "")
    market_research = state.get("market_research", "")

    if not context:
        return {**state, "swot_analysis": "No data available for SWOT analysis.", "opportunity_assessment": ""}

    prompt = f"""Using the data and prior agent analyses below, generate a comprehensive SWOT Analysis
and Product Opportunity Assessment.

BUSINESS DATA SUMMARY:
{context[:2000]}

CUSTOMER INSIGHTS:
{customer_insights[:600] if customer_insights else 'N/A'}

MARKET RESEARCH:
{market_research[:600] if market_research else 'N/A'}

Generate:

## SWOT ANALYSIS

**STRENGTHS** (internal positives — what's working well)
- List 5-7 specific strengths backed by data (e.g., high-rated products, strong revenue categories)

**WEAKNESSES** (internal negatives — what needs improvement)
- List 4-6 specific weaknesses backed by data (e.g., high return rates, low margin products)

**OPPORTUNITIES** (external — what can be capitalized on)
- List 5-7 specific opportunities (e.g., underserved regions, growing categories, low competition signals)

**THREATS** (external — risks to watch)
- List 4-5 specific threats (e.g., customer dissatisfaction trends, declining segments)

## PRODUCT OPPORTUNITY ASSESSMENT

For each major product/category, provide an opportunity score (1-10) with brief justification:
Format: Product Name | Score (X/10) | Key Opportunity | Risk Factor

## KEY STRATEGIC IMPLICATIONS
- 3-5 bullet points summarizing the most critical strategic takeaways from this SWOT"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=500,
    )

    full_output = response.choices[0].message.content

    # Split SWOT from opportunity assessment for separate storage
    swot_part = full_output
    opp_part = ""
    if "## PRODUCT OPPORTUNITY ASSESSMENT" in full_output:
        parts = full_output.split("## PRODUCT OPPORTUNITY ASSESSMENT", 1)
        swot_part = parts[0].strip()
        opp_part = "## PRODUCT OPPORTUNITY ASSESSMENT\n" + parts[1].strip()

    return {
        **state,
        "swot_analysis": swot_part,
        "opportunity_assessment": opp_part,
    }
