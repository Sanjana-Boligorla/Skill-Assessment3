from utils.llm_client import get_client


SYSTEM_PROMPT = """You are an Executive Report Agent — a C-suite communication specialist who distills
complex multi-agent analyses into crisp, executive-ready summaries.

Your role is to:
- Write a compelling executive summary that a CEO/CPO can read in 3 minutes
- Highlight the 3 most critical insights across all analyses
- Summarize key decisions that need to be made
- Use executive language: clear, direct, data-backed, no jargon
- Structure for a board presentation"""


def run(state: dict) -> dict:
    client = get_client()

    customer_insights = state.get("customer_insights", "")
    market_research = state.get("market_research", "")
    swot = state.get("swot_analysis", "")
    opportunity = state.get("opportunity_assessment", "")
    prioritization = state.get("feature_prioritization", "")
    strategy = state.get("strategy_recommendations", "")

    all_analyses = f"""
CUSTOMER INSIGHTS:
{customer_insights[:500] if customer_insights else 'N/A'}

MARKET RESEARCH:
{market_research[:500] if market_research else 'N/A'}

SWOT ANALYSIS:
{swot[:500] if swot else 'N/A'}

OPPORTUNITY ASSESSMENT:
{opportunity[:300] if opportunity else 'N/A'}

FEATURE PRIORITIES:
{prioritization[:400] if prioritization else 'N/A'}

STRATEGY RECOMMENDATIONS:
{strategy[:500] if strategy else 'N/A'}
"""

    prompt = f"""Synthesize all agent analyses into an Executive Summary for senior leadership.

COMPLETE ANALYSES:
{all_analyses}

Write a board-ready Executive Summary with:

## EXECUTIVE SUMMARY

### Business Situation
2-3 sentences: current performance state backed by key numbers

### Critical Findings
**Finding 1:** [Most important insight with supporting data]
**Finding 2:** [Second key insight]
**Finding 3:** [Third key insight]

### Top 3 Strategic Priorities
1. [Priority] — [One-line business case] — [Expected outcome]
2. [Priority] — [One-line business case] — [Expected outcome]
3. [Priority] — [One-line business case] — [Expected outcome]

### Decisions Required
- [Decision 1 that leadership needs to make]
- [Decision 2]
- [Decision 3]

### 12-Month Outlook
2-3 sentences on projected trajectory if recommendations are followed vs not followed.

### Bottom Line
One powerful paragraph (3-4 sentences) summarizing the entire strategic situation and call to action.

Keep language executive-level: direct, data-backed, action-oriented."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=500,
    )

    executive_summary = response.choices[0].message.content

    # Compile key metrics for PDF report header
    parsed_files = state.get("parsed_files", [])
    key_metrics = {}
    for f in parsed_files:
        if f.get("type") == "csv":
            key_metrics = {
                "Total Revenue": f"${f.get('total_revenue', 0):,.2f}",
                "Total Profit": f"${f.get('total_profit', 0):,.2f}",
                "Total Units Sold": f"{f.get('total_units', 0):,}",
                "Avg Customer Rating": f"{f.get('avg_rating', 0)}/5.0",
                "Total Returns": str(f.get("total_returns", 0)),
                "Date Range": f.get("date_range", "N/A"),
                "Products Analyzed": str(len(f.get("products", []))),
                "Regions Covered": str(len(f.get("regions", []))),
            }
            break

    return {
        **state,
        "executive_summary": executive_summary,
        "key_metrics": key_metrics,
        "pipeline_complete": True,
    }
