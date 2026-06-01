from utils.llm_client import get_client


SYSTEM_PROMPT = """You are a Strategy Recommendation Agent — a senior product strategist who synthesizes
all available analyses into concrete, executable strategic recommendations.

Your role is to:
- Generate a Strategic Action Plan with clear priorities and timelines
- Produce Product Roadmap Suggestions (Now / Next / Later framework)
- Define success metrics for each strategic initiative
- Identify dependencies and risks
- Translate insights into board-ready strategic recommendations

Be concrete, specific, and actionable. Tie every recommendation back to data evidence."""


def run(state: dict) -> dict:
    client = get_client()
    context = state.get("data_context", "")
    customer_insights = state.get("customer_insights", "")
    market_research = state.get("market_research", "")
    swot = state.get("swot_analysis", "")
    opportunity = state.get("opportunity_assessment", "")
    prioritization = state.get("feature_prioritization", "")

    if not context:
        return {**state, "strategy_recommendations": "No data available for strategy recommendations."}

    prompt = f"""You are synthesizing all prior agent analyses into a final Strategic Recommendations report.

DATA CONTEXT SUMMARY:
{context[:1500]}

PRIOR ANALYSES SUMMARY:
- Customer Insights: {customer_insights[:300] if customer_insights else 'N/A'}
- Market Research: {market_research[:300] if market_research else 'N/A'}
- SWOT: {swot[:300] if swot else 'N/A'}
- Opportunities: {opportunity[:200] if opportunity else 'N/A'}
- Feature Priorities: {prioritization[:300] if prioritization else 'N/A'}

Generate a comprehensive Strategic Recommendations Report:

## STRATEGIC ACTION PLAN

### Immediate Actions (0-3 months)
For each action: What | Why (data evidence) | Expected Impact | Owner (role)

### Short-Term Initiatives (3-6 months)
For each: Initiative | Business Case | KPIs to Track

### Medium-Term Strategy (6-12 months)
For each: Strategic Goal | Approach | Success Metrics

## PRODUCT ROADMAP SUGGESTIONS

### NOW (Current Quarter)
- Specific product/feature work to start immediately

### NEXT (Next Quarter)
- Planned initiatives with prerequisites

### LATER (6-12 months)
- Strategic bets and longer-horizon investments

## REVENUE GROWTH STRATEGY
- Top 3 revenue acceleration opportunities with projected impact

## RISK MITIGATION PLAN
- Top 3 risks identified and specific mitigation actions

## SUCCESS METRICS DASHBOARD
Key metrics to track progress:
| Metric | Current Baseline | 3-Month Target | 12-Month Target |

## STRATEGIC PRIORITIES SUMMARY
Top 5 strategic priorities ranked by business impact, with one-line rationale each."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_completion_tokens=500,
    )

    recommendations = response.choices[0].message.content
    return {**state, "strategy_recommendations": recommendations}
