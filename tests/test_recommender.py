import pytest
import os
from src.recommender import recommend
from src.categories import DATA_DIR


@pytest.fixture(autouse=True)
def clean_update_queue():
    queue_file = DATA_DIR / "update_queue.jsonl"
    if queue_file.exists():
        queue_file.unlink()
    yield
    if queue_file.exists():
        queue_file.unlink()


class TestStarbucksQuery:
    def test_correct_card(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["recommended_card"] == "Max Cashback+"

    def test_confidence(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["confidence"] == "high"

    def test_match_type(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["match_type"] == "exact"

    def test_category(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["resolved_category"] == "dining"

    def test_no_update_needed(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["update_needed"] is False

    def test_reward_rate(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["reward_rate"] == 5.0

    def test_estimated_reward(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert result["estimated_reward"] == 0.62


class TestAmazonSGQuery:
    def test_correct_card(self):
        result = recommend("Amazon SG", "shopping", 84.20, ["Max Online Rewards", "Max Everyday Mastercard"])
        assert result["recommended_card"] == "Max Online Rewards"

    def test_fuzzy_match(self):
        result = recommend("Amazon SG", "shopping", 84.20, ["Max Online Rewards", "Max Everyday Mastercard"])
        assert result["match_type"] == "fuzzy"

    def test_confidence(self):
        result = recommend("Amazon SG", "shopping", 84.20, ["Max Online Rewards", "Max Everyday Mastercard"])
        assert result["confidence"] == "medium"

    def test_category(self):
        result = recommend("Amazon SG", "shopping", 84.20, ["Max Online Rewards", "Max Everyday Mastercard"])
        assert result["resolved_category"] == "online_shopping"


class TestDonDonDonkiQuery:
    def test_correct_card(self):
        result = recommend("Don Don Donki", "groceries", 45.00, ["Max Cashback+", "Max Everyday Mastercard"])
        assert result["recommended_card"] == "Max Cashback+"

    def test_hint_fallback(self):
        result = recommend("Don Don Donki", "groceries", 45.00, ["Max Cashback+", "Max Everyday Mastercard"])
        assert result["match_type"] == "hint_fallback"

    def test_low_confidence(self):
        result = recommend("Don Don Donki", "groceries", 45.00, ["Max Cashback+", "Max Everyday Mastercard"])
        assert result["confidence"] == "low"

    def test_update_needed(self):
        result = recommend("Don Don Donki", "groceries", 45.00, ["Max Cashback+", "Max Everyday Mastercard"])
        assert result["update_needed"]["type"] == "low_confidence_inference"

    def test_estimated_reward(self):
        result = recommend("Don Don Donki", "groceries", 45.00, ["Max Cashback+", "Max Everyday Mastercard"])
        assert result["estimated_reward"] == 1.80


class TestAgodaQuery:
    def test_correct_card(self):
        result = recommend("Agoda", "travel", 220.00, ["Max Travel Visa", "Max Cashback+"])
        assert result["recommended_card"] == "Max Travel Visa"

    def test_exact_match(self):
        result = recommend("Agoda", "travel", 220.00, ["Max Travel Visa", "Max Cashback+"])
        assert result["match_type"] == "exact"

    def test_confidence(self):
        result = recommend("Agoda", "travel", 220.00, ["Max Travel Visa", "Max Cashback+"])
        assert result["confidence"] == "high"

    def test_category(self):
        result = recommend("Agoda", "travel", 220.00, ["Max Travel Visa", "Max Cashback+"])
        assert result["resolved_category"] == "hotels"

    def test_no_update(self):
        result = recommend("Agoda", "travel", 220.00, ["Max Travel Visa", "Max Cashback+"])
        assert result["update_needed"] is False


class TestEdgeCases:
    def test_unknown_merchant_no_hint(self):
        result = recommend("XYZZY Corp", None, 50.00, ["Max Cashback+"])
        assert result["confidence"] == "low"
        assert result["resolved_category"] == "general"
        assert result["update_needed"]["needs_update"] is True

    def test_unknown_card(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Nonexistent Card"])
        assert result["recommended_card"] is None
        assert "warnings" in result

    def test_no_cards_shows_top_3(self):
        result = recommend("Starbucks", "coffee", 12.50)
        assert "top_cards" in result
        assert len(result["top_cards"]) == 3

    def test_empty_merchant(self):
        result = recommend("", "coffee", 10.00, ["Max Cashback+"])
        assert result["resolved_category"] == "dining"

    def test_messy_merchant_string(self):
        result = recommend("STARBUCKS #12345 PTE LTD", "coffee", 12.50, ["Max Cashback+"])
        assert result["recommended_card"] == "Max Cashback+"
        assert result["match_type"] == "exact"

    def test_keyword_inference(self):
        result = recommend("Blue Bottle Coffee", None, 8.00, ["Max Cashback+"])
        assert result["match_type"] == "keyword"
        assert result["resolved_category"] == "dining"
        assert result["update_needed"]["type"] == "merchant_missing"

    def test_category_mismatch_flagged(self):
        result = recommend("Starbucks", "transport", 12.50, ["Max Cashback+"])
        assert result["update_needed"]["type"] == "category_mismatch"

    def test_explanation_present(self):
        result = recommend("Starbucks", "coffee", 12.50, ["Max Cashback+", "Max Travel Visa"])
        assert len(result["explanation"]) > 0
        assert "Max Cashback+" in result["explanation"]

    def test_travel_hint_group_resolution(self):
        result = recommend("XYZZY Corp", "travel", 100.00, ["Max Travel Visa", "Max Online Rewards"])
        assert result["recommended_card"] == "Max Online Rewards"
        assert result["reward_rate"] == 5.0


class TestUpdateQueue:
    def test_update_written_to_file(self):
        queue_file = DATA_DIR / "update_queue.jsonl"
        recommend("Don Don Donki", "groceries", 45.00, ["Max Cashback+"])
        assert queue_file.exists()
        with open(queue_file) as f:
            lines = f.readlines()
        assert len(lines) >= 1

    def test_no_update_no_file(self):
        queue_file = DATA_DIR / "update_queue.jsonl"
        recommend("Starbucks", "coffee", 12.50, ["Max Cashback+"])
        assert not queue_file.exists()
