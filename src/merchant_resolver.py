import json
from rapidfuzz import fuzz, process, utils as rfuzz_utils
from src.categories import (
    load_category_aliases,
    load_category_descriptors,
    resolve_hint,
    categories_in_same_group,
    CATEGORY_GROUPS,
    DATA_DIR,
)
from src.preprocess import normalize_merchant

FUZZY_ACCEPT_THRESHOLD = 60
FUZZY_ALIAS_THRESHOLD = 80


def load_merchants():
    with open(DATA_DIR / "merchants.json") as f:
        merchants = json.load(f)
    return {m["normalized_name"]: m for m in merchants}


def exact_lookup(normalized_name, merchants_db, hint=None, aliases=None):
    if normalized_name not in merchants_db:
        return None

    merchant = merchants_db[normalized_name]
    category = merchant["category"]

    result = {
        "category": category,
        "confidence": "high",
        "match_type": "exact",
        "matched_merchant": merchant["merchant_name"],
        "update_needed": False,
    }

    if hint:
        resolved = resolve_hint(hint, aliases)
        if resolved is not None and not isinstance(resolved, list):
            if not categories_in_same_group(resolved, category) and resolved != category:
                result["update_needed"] = {
                    "needs_update": True,
                    "type": "category_mismatch",
                    "reason": f"Merchant '{merchant['merchant_name']}' is categorized as '{category}' but hint '{hint}' suggests '{resolved}'",
                }

    return result


def fuzzy_match(normalized_name, merchants_db):
    merchant_names = list(merchants_db.keys())
    if not merchant_names:
        return None

    result = process.extractOne(
        normalized_name,
        merchant_names,
        scorer=fuzz.WRatio,
        processor=rfuzz_utils.default_process,
    )

    if result is None:
        return None

    match_name, score, _ = result

    if score < FUZZY_ACCEPT_THRESHOLD:
        return None

    merchant = merchants_db[match_name]
    category = merchant["category"]

    update_needed = False
    if score < FUZZY_ALIAS_THRESHOLD:
        update_needed = {
            "needs_update": True,
            "type": "merchant_alias",
            "reason": f"'{normalized_name}' matched '{match_name}' (score: {score:.0f}). Consider adding as known alias.",
        }

    return {
        "category": category,
        "confidence": "medium",
        "match_type": "fuzzy",
        "matched_merchant": merchant["merchant_name"],
        "fuzzy_score": score,
        "update_needed": update_needed,
    }


def keyword_match(normalized_name, descriptors=None):
    if descriptors is None:
        descriptors = load_category_descriptors()

    merchant_words = set(normalized_name.split())

    scores = {}
    for category, descriptor_list in descriptors.items():
        hits = 0
        for descriptor in descriptor_list:
            descriptor_words = set(descriptor.lower().split())
            if descriptor_words & merchant_words:
                hits += 1
        if hits > 0:
            scores[category] = hits

    if not scores:
        return None

    best_category = max(scores, key=scores.get)
    return best_category


def keyword_and_hint_inference(normalized_name, hint=None, aliases=None, descriptors=None):
    if aliases is None:
        aliases = load_category_aliases()
    if descriptors is None:
        descriptors = load_category_descriptors()

    keyword_category = keyword_match(normalized_name, descriptors)

    if keyword_category:
        return {
            "category": keyword_category,
            "confidence": "low",
            "match_type": "keyword",
            "update_needed": {
                "needs_update": True,
                "type": "merchant_missing",
                "reason": f"Merchant '{normalized_name}' not in DB. Inferred category: {keyword_category}",
            },
        }

    resolved = resolve_hint(hint, aliases)

    if isinstance(resolved, list):
        return {
            "category": resolved,
            "confidence": "low",
            "match_type": "hint_fallback",
            "hint_group": True,
            "update_needed": {
                "needs_update": True,
                "type": "low_confidence_inference",
                "reason": f"Merchant '{normalized_name}' unresolved. Used category hint group: '{hint}'",
            },
        }

    if resolved:
        return {
            "category": resolved,
            "confidence": "low",
            "match_type": "hint_fallback",
            "update_needed": {
                "needs_update": True,
                "type": "low_confidence_inference",
                "reason": f"Merchant '{normalized_name}' unresolved. Used category hint: '{hint}'",
            },
        }

    return {
        "category": "general",
        "confidence": "low",
        "match_type": "hint_fallback",
        "update_needed": {
            "needs_update": True,
            "type": "low_confidence_inference",
            "reason": f"Merchant '{normalized_name}' unresolved. No hint provided, defaulting to general.",
        },
    }


def resolve_merchant(merchant_name, hint=None):
    normalized = normalize_merchant(merchant_name)
    merchants_db = load_merchants()
    aliases = load_category_aliases()
    descriptors = load_category_descriptors()

    result = exact_lookup(normalized, merchants_db, hint, aliases)
    if result:
        result["resolved_merchant"] = normalized
        return result

    result = fuzzy_match(normalized, merchants_db)
    if result:
        result["resolved_merchant"] = normalized
        return result

    result = keyword_and_hint_inference(normalized, hint, aliases, descriptors)
    result["resolved_merchant"] = normalized
    return result
