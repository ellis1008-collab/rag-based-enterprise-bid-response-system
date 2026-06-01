from collections import Counter

from app.agents.state import BidAgentState


def assess_risk_node(state: BidAgentState) -> dict:
    responses = state.get("responses", [])
    match_counts = Counter(response["match_status"] for response in responses)
    risk_counts = Counter(response["risk_level"] for response in responses)

    return {
        "risk_summary": {
            "match_status_counts": {
                "satisfied": match_counts["satisfied"],
                "partial": match_counts["partial"],
                "unsupported": match_counts["unsupported"],
            },
            "risk_level_counts": {
                "low": risk_counts["low"],
                "medium": risk_counts["medium"],
                "high": risk_counts["high"],
            },
        }
    }
