import pytest
from src.card_ranker import rank_cards, get_reward_rate, load_cards


@pytest.fixture
def cards():
    return load_cards()


class TestGetRewardRate:
    def test_specific_category(self, cards):
        rate, cat = get_reward_rate(cards[0], "airlines")
        assert rate == 4.0
        assert cat == "airlines"

    def test_fallback_to_general(self, cards):
        rate, cat = get_reward_rate(cards[0], "groceries")
        assert rate == 1.2
        assert cat == "general"

    def test_no_general_rate(self):
        card = {"earn_rules": [{"category": "dining", "reward_rate": 5.0}]}
        rate, cat = get_reward_rate(card, "groceries")
        assert rate == 0.0

    def test_category_list(self, cards):
        rate, cat = get_reward_rate(cards[0], ["airlines", "hotels", "travel_portal"])
        assert rate == 4.0
        assert cat in ("airlines", "hotels")

    def test_category_list_picks_best(self):
        card = {
            "earn_rules": [
                {"category": "airlines", "reward_rate": 2.0},
                {"category": "hotels", "reward_rate": 5.0},
            ]
        }
        rate, cat = get_reward_rate(card, ["airlines", "hotels"])
        assert rate == 5.0
        assert cat == "hotels"


class TestRankCards:
    def test_dining_ranking(self):
        result = rank_cards("dining", 100.0, ["Max Cashback+", "Max Travel Visa"])
        ranked = result["ranked_cards"]
        assert ranked[0]["card_name"] == "Max Cashback+"
        assert ranked[0]["reward_rate"] == 5.0

    def test_online_shopping_ranking(self):
        result = rank_cards("online_shopping", 100.0, ["Max Online Rewards", "Max Everyday Mastercard"])
        ranked = result["ranked_cards"]
        assert ranked[0]["card_name"] == "Max Online Rewards"
        assert ranked[0]["reward_rate"] == 6.0

    def test_estimated_reward_calculation(self):
        result = rank_cards("dining", 12.50, ["Max Cashback+"])
        ranked = result["ranked_cards"]
        assert ranked[0]["estimated_reward"] == 0.62

    def test_no_cards_ranks_all(self):
        result = rank_cards("dining", 100.0)
        assert len(result["ranked_cards"]) == 4

    def test_unknown_card_warning(self):
        result = rank_cards("dining", 100.0, ["Max Cashback+", "Nonexistent Card"])
        assert "Nonexistent Card" in result["unknown_cards"]
        assert len(result["ranked_cards"]) == 1

    def test_all_unknown_cards(self):
        result = rank_cards("dining", 100.0, ["Fake Card 1", "Fake Card 2"])
        assert len(result["ranked_cards"]) == 0

    def test_general_fallback(self):
        result = rank_cards("entertainment", 100.0, ["Max Travel Visa"])
        ranked = result["ranked_cards"]
        assert ranked[0]["reward_rate"] == 1.2
        assert ranked[0]["matched_category"] == "general"

    def test_close_call_detection(self):
        result = rank_cards("hotels", 100.0)
        if result["close_call"]:
            assert result["update_needed"]["type"] == "card_rule_ambiguous"

    def test_confidence_downgrade_on_close_call(self):
        result = rank_cards("hotels", 100.0, confidence="high")
        if result["close_call"]:
            assert result["confidence"] == "medium"

    def test_no_close_call_preserves_confidence(self):
        result = rank_cards("dining", 100.0, ["Max Cashback+", "Max Travel Visa"], confidence="high")
        assert result["confidence"] == "high"

    def test_category_list_ranking(self):
        result = rank_cards(
            ["airlines", "hotels", "travel_portal"],
            220.0,
            ["Max Travel Visa", "Max Cashback+"],
        )
        ranked = result["ranked_cards"]
        assert ranked[0]["card_name"] == "Max Travel Visa"

    def test_transport_ranking(self):
        result = rank_cards("transport", 50.0, ["Max Everyday Mastercard", "Max Cashback+"])
        ranked = result["ranked_cards"]
        assert ranked[0]["card_name"] == "Max Everyday Mastercard"
        assert ranked[0]["reward_rate"] == 3.0
