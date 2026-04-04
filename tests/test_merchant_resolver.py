import pytest
from src.merchant_resolver import (
    exact_lookup,
    fuzzy_match,
    keyword_match,
    keyword_and_hint_inference,
    resolve_merchant,
    load_merchants,
)
from src.categories import load_category_aliases, load_category_descriptors


@pytest.fixture
def merchants_db():
    return load_merchants()


@pytest.fixture
def aliases():
    return load_category_aliases()


@pytest.fixture
def descriptors():
    return load_category_descriptors()


class TestExactLookup:
    def test_known_merchant(self, merchants_db):
        result = exact_lookup("starbucks", merchants_db)
        assert result is not None
        assert result["category"] == "dining"
        assert result["confidence"] == "high"
        assert result["match_type"] == "exact"

    def test_unknown_merchant(self, merchants_db):
        result = exact_lookup("unknown_place", merchants_db)
        assert result is None

    def test_hint_matches(self, merchants_db, aliases):
        result = exact_lookup("starbucks", merchants_db, hint="coffee", aliases=aliases)
        assert result["update_needed"] is False

    def test_hint_mismatch(self, merchants_db, aliases):
        result = exact_lookup("starbucks", merchants_db, hint="transport", aliases=aliases)
        assert result["update_needed"]["type"] == "category_mismatch"

    def test_hint_same_group(self, merchants_db, aliases):
        result = exact_lookup("agoda", merchants_db, hint="airlines", aliases=aliases)
        assert result["update_needed"] is False

    def test_all_merchants_found(self, merchants_db):
        for name in ["amazon", "shopee", "starbucks", "grab", "agoda"]:
            result = exact_lookup(name, merchants_db)
            assert result is not None, f"Expected {name} to be found"


class TestFuzzyMatch:
    def test_close_match_high_score(self, merchants_db):
        result = fuzzy_match("amazon sg", merchants_db)
        assert result is not None
        assert result["category"] == "online_shopping"
        assert result["confidence"] == "medium"
        assert result["fuzzy_score"] >= 80

    def test_no_match(self, merchants_db):
        result = fuzzy_match("xyzzy corp", merchants_db)
        assert result is None

    def test_typo_match(self, merchants_db):
        result = fuzzy_match("starbux", merchants_db)
        assert result is not None
        assert result["category"] == "dining"

    def test_low_score_flags_alias(self, merchants_db):
        result = fuzzy_match("starbux", merchants_db)
        if result and result["fuzzy_score"] < 80:
            assert result["update_needed"]["type"] == "merchant_alias"

    def test_high_score_no_alias_flag(self, merchants_db):
        result = fuzzy_match("amazon sg", merchants_db)
        assert result["update_needed"] is False

    def test_grab_car(self, merchants_db):
        result = fuzzy_match("grab car", merchants_db)
        assert result is not None
        assert result["category"] == "transport"

    def test_ntuc(self, merchants_db):
        result = fuzzy_match("ntuc", merchants_db)
        assert result is not None
        assert result["category"] == "groceries"


class TestKeywordMatch:
    def test_coffee_matches_dining(self, descriptors):
        result = keyword_match("blue bottle coffee", descriptors)
        assert result == "dining"

    def test_hotel_matches_hotels(self, descriptors):
        result = keyword_match("grand hotel", descriptors)
        assert result == "hotels"

    def test_airline_matches(self, descriptors):
        result = keyword_match("budget airline", descriptors)
        assert result == "airlines"

    def test_no_keyword_match(self, descriptors):
        result = keyword_match("don don donki", descriptors)
        assert result is None

    def test_taxi_matches_transport(self, descriptors):
        result = keyword_match("city taxi", descriptors)
        assert result == "transport"

    def test_supermarket_matches_groceries(self, descriptors):
        result = keyword_match("mega supermarket", descriptors)
        assert result == "groceries"


class TestKeywordAndHintInference:
    def test_keyword_hit(self, aliases, descriptors):
        result = keyword_and_hint_inference("blue bottle coffee", aliases=aliases, descriptors=descriptors)
        assert result["category"] == "dining"
        assert result["match_type"] == "keyword"
        assert result["update_needed"]["type"] == "merchant_missing"

    def test_hint_fallback(self, aliases, descriptors):
        result = keyword_and_hint_inference("don don donki", hint="groceries", aliases=aliases, descriptors=descriptors)
        assert result["category"] == "groceries"
        assert result["match_type"] == "hint_fallback"
        assert result["update_needed"]["type"] == "low_confidence_inference"

    def test_no_keyword_no_hint(self, aliases, descriptors):
        result = keyword_and_hint_inference("xyzzy corp", aliases=aliases, descriptors=descriptors)
        assert result["category"] == "general"
        assert result["match_type"] == "hint_fallback"

    def test_hint_alias_resolution(self, aliases, descriptors):
        result = keyword_and_hint_inference("xyzzy corp", hint="coffee", aliases=aliases, descriptors=descriptors)
        assert result["category"] == "dining"

    def test_hint_group_resolution(self, aliases, descriptors):
        result = keyword_and_hint_inference("xyzzy corp", hint="travel", aliases=aliases, descriptors=descriptors)
        assert isinstance(result["category"], list)
        assert "airlines" in result["category"]
        assert "hotels" in result["category"]

    def test_always_flags_update(self, aliases, descriptors):
        result = keyword_and_hint_inference("anything", hint="coffee", aliases=aliases, descriptors=descriptors)
        assert result["update_needed"]["needs_update"] is True


class TestResolveMerchant:
    def test_exact_path(self):
        result = resolve_merchant("Starbucks")
        assert result["match_type"] == "exact"
        assert result["category"] == "dining"
        assert result["confidence"] == "high"

    def test_fuzzy_path(self):
        result = resolve_merchant("Amazon SG")
        assert result["match_type"] == "fuzzy"
        assert result["category"] == "online_shopping"
        assert result["confidence"] == "medium"

    def test_keyword_path(self):
        result = resolve_merchant("Blue Bottle Coffee")
        assert result["match_type"] == "keyword"
        assert result["category"] == "dining"
        assert result["confidence"] == "low"

    def test_hint_fallback_path(self):
        result = resolve_merchant("Don Don Donki", hint="groceries")
        assert result["match_type"] == "hint_fallback"
        assert result["category"] == "groceries"
        assert result["confidence"] == "low"

    def test_no_match_no_hint(self):
        result = resolve_merchant("XYZZY Corp")
        assert result["match_type"] == "hint_fallback"
        assert result["category"] == "general"

    def test_resolved_merchant_field(self):
        result = resolve_merchant("STARBUCKS #12345 PTE LTD")
        assert result["resolved_merchant"] == "starbucks"
