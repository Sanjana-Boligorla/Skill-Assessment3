from utils.llm_client import get_client


SYSTEM_PROMPT = """You are a Feature Prioritization Agent specializing in product portfolio management
and feature investment decisions.

You use frameworks like RICE (Reach, Impact, Confidence, Effort) and ICE scoring to prioritize
product improvements and new features based on business data, customer feedback, and strategic goals.

Your role is to:
- Identify which products need investment vs optimization vs harvest decisions
- Score and rank feature/product improvement opportunities
- Use profit margins, ratings, return rates, and customer feedback as prioritization signals
- Recommend a prioritized backlog of product improvements
- Apply the 80/20 principle to focus on highest-impact items"""


def run(state: dict) -> dict:
    client = get_client()
    context = state.get("data_context", "")
    customer_insights = state.get("customer_insights", "")
    swot = state.get("swot_analysis", "")
    opportunity = state.get("opportunity_assessment", "")

    if not context:
        return {**state, "feature_prioritization": "No data available for feature prioritization."}

    prompt = f"""Based on the following data and analyses, generate a Feature Prioritization Report.

BUSINESS DATA SUMMARY:
{context[:2000]}

CUSTOMER INSIGHTS SUMMARY:
{customer_insights[:400] if customer_insights else 'N/A'}

SWOT HIGHLIGHTS:
{swot[:400] if swot else 'N/A'}

OPPORTUNITY ASSESSMENT:
{opportunity[:400] if opportunity else 'N/A'}

Generate a comprehensive Feature Prioritization Report:

## PORTFOLIO INVESTMENT STRATEGY
Categorize each product into: INVEST (grow), OPTIMIZE (improve), HARVEST (maintain/phase):
| Product | Category | Decision | Rationale |

## PRIORITIZED FEATURE/IMPROVEMENT BACKLOG
Using ICE Score (Impact × Confidence ÷ Effort, scale 1-10 each):

### CRITICAL PRIORITY (Score 60+)
List top improvements with ICE scores and business justification

### HIGH PRIORITY (Score 40-59)
List improvements with ICE scores

### MEDIUM PRIORITY (Score 20-39)
List improvements with ICE scores

## PRODUCT IMPROVEMENT RECOMMENDATIONS
For the top 3 products by opportunity, list specific, actionable improvements:
- What to improve and why (backed by customer feedback/ratings/returns data)

## QUICK WINS (High Impact, Low Effort)
- 3-5 immediately actionable improvements that can be done quickly

## RESOURCE ALLOCATION RECOMMENDATION
- Where to focus product development budget (%) across categories"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=500,
    )

    prioritization = response.choices[0].message.content
    return {**state, "feature_prioritization": prioritization}
