from src.merchant_resolver import resolve_merchant
from src.card_ranker import rank_cards
from src.update_queue import append_update


def build_explanation(top_card, ranked_cards, category, close_call):
    cat_label = category if isinstance(category, str) else top_card["matched_category"]
    top = top_card
    line = (
        f"{top['card_name']} earns {top['reward_rate']}% on {cat_label} "
        f"(${top['estimated_reward']:.2f} on this purchase)"
    )

    if len(ranked_cards) >= 2:
        second = ranked_cards[1]
        if close_call:
            line += (
                f", but {second['card_name']} is close at {second['reward_rate']}% "
                f"(${second['estimated_reward']:.2f}). "
                f"Consider other factors like spending caps or sign-up bonuses."
            )
        else:
            line += (
                f", compared to {second['card_name']} at {second['reward_rate']}% "
                f"(${second['estimated_reward']:.2f})."
            )
    else:
        line += "."

    return line


def collect_updates(merchant_update, card_update):
    updates = []
    if merchant_update and merchant_update is not False:
        updates.append(merchant_update)
    if card_update and card_update is not False:
        updates.append(card_update)

    if not updates:
        return False
    if len(updates) == 1:
        return updates[0]
    return updates


def recommend(merchant, category_hint=None, amount=0.0, user_cards=None):
    resolution = resolve_merchant(merchant, hint=category_hint)

    category = resolution["category"]
    confidence = resolution["confidence"]
    match_type = resolution["match_type"]

    ranking = rank_cards(
        category=category,
        amount=amount,
        user_card_names=user_cards,
        confidence=confidence,
    )

    confidence = ranking["confidence"]
    ranked = ranking["ranked_cards"]

    update_needed = collect_updates(resolution.get("update_needed"), ranking.get("update_needed"))

    if not ranked:
        result = {
            "recommended_card": None,
            "reward_rate": 0.0,
            "estimated_reward": 0.0,
            "explanation": "No matching cards found.",
            "confidence": confidence,
            "resolved_merchant": resolution["resolved_merchant"],
            "resolved_category": category if isinstance(category, str) else category[0],
            "match_type": match_type,
            "update_needed": update_needed,
        }
        if ranking["unknown_cards"]:
            result["warnings"] = [f"Card not found: {c}" for c in ranking["unknown_cards"]]
        return result

    top = ranked[0]
    show_cards = ranked if user_cards else ranked[:3]

    resolved_cat = top["matched_category"] if isinstance(category, list) else category

    explanation = build_explanation(top, ranked, category, ranking["close_call"])

    if update_needed:
        entries = update_needed if isinstance(update_needed, list) else [update_needed]
        for entry in entries:
            append_update(merchant, entry, match_type, resolved_cat)

    result = {
        "recommended_card": top["card_name"],
        "reward_rate": top["reward_rate"],
        "estimated_reward": top["estimated_reward"],
        "explanation": explanation,
        "confidence": confidence,
        "resolved_merchant": resolution["resolved_merchant"],
        "resolved_category": resolved_cat,
        "match_type": match_type,
        "update_needed": update_needed,
    }

    if not user_cards:
        result["top_cards"] = show_cards

    if ranking["unknown_cards"]:
        result["warnings"] = [f"Card not found: {c}" for c in ranking["unknown_cards"]]

    return result
