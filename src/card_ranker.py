import json
from src.categories import DATA_DIR

CLOSE_CALL_THRESHOLD = 0.20

CONFIDENCE_DOWNGRADE = {
    "high": "medium",
    "medium": "low",
    "low": "low",
}


def load_cards():
    with open(DATA_DIR / "cards.json") as f:
        return json.load(f)


def get_reward_rate(card, category):
    if isinstance(category, list):
        results = [get_reward_rate(card, cat) for cat in category]
        return max(results, key=lambda x: x[0])

    rules = {r["category"]: r["reward_rate"] for r in card["earn_rules"]}

    if category in rules:
        return rules[category], category

    if "general" in rules:
        return rules["general"], "general"

    return 0.0, category


def rank_cards(category, amount, user_card_names=None, confidence="high"):
    all_cards = load_cards()

    if user_card_names:
        cards = [c for c in all_cards if c["card_name"] in user_card_names]
        unknown = set(user_card_names) - {c["card_name"] for c in cards}
    else:
        cards = all_cards
        unknown = set()

    if not cards:
        return {
            "ranked_cards": [],
            "confidence": confidence,
            "close_call": False,
            "unknown_cards": list(unknown),
            "update_needed": False,
        }

    ranked = []
    for card in cards:
        rate, resolved_cat = get_reward_rate(card, category)

        reward = rate / 100 * amount
        ranked.append({
            "card_name": card["card_name"],
            "card_id": card["card_id"],
            "reward_rate": rate,
            "estimated_reward": round(reward, 2),
            "matched_category": resolved_cat,
        })

    ranked.sort(key=lambda x: x["reward_rate"], reverse=True)

    close_call = False
    update_needed = False

    if len(ranked) >= 2:
        top_rate = ranked[0]["reward_rate"]
        second_rate = ranked[1]["reward_rate"]
        if top_rate > 0 and second_rate > 0:
            gap = (top_rate - second_rate) / top_rate
            if gap <= CLOSE_CALL_THRESHOLD:
                close_call = True
                confidence = CONFIDENCE_DOWNGRADE[confidence]
                update_needed = {
                    "needs_update": True,
                    "type": "card_rule_ambiguous",
                    "reason": (
                        f"'{ranked[0]['card_name']}' ({top_rate}%) and "
                        f"'{ranked[1]['card_name']}' ({second_rate}%) are within "
                        f"{CLOSE_CALL_THRESHOLD * 100:.0f}% of each other"
                    ),
                }

    return {
        "ranked_cards": ranked,
        "confidence": confidence,
        "close_call": close_call,
        "unknown_cards": list(unknown),
        "update_needed": update_needed,
    }
