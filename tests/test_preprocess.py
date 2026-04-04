import pytest
from src.preprocess import normalize_merchant


class TestNormalizeMerchant:
    def test_lowercase(self):
        assert normalize_merchant("STARBUCKS") == "starbucks"

    def test_strip_store_id_hash(self):
        assert normalize_merchant("STARBUCKS #12345") == "starbucks"

    def test_strip_store_id_asterisk(self):
        assert normalize_merchant("GRAB* A-4KXYZW") == "grab"

    def test_remove_corporate_suffixes(self):
        assert normalize_merchant("Starbucks PTE LTD") == "starbucks"

    def test_remove_multiple_suffixes(self):
        assert normalize_merchant("Company Corp Inc") == "company"

    def test_remove_punctuation(self):
        assert normalize_merchant("Star-bucks!") == "starbucks"

    def test_collapse_whitespace(self):
        assert normalize_merchant("  Amazon   SG  ") == "amazon sg"

    def test_preserve_meaningful_words(self):
        assert normalize_merchant("Amazon SG") == "amazon sg"

    def test_empty_string(self):
        assert normalize_merchant("") == ""

    def test_none(self):
        assert normalize_merchant(None) == ""

    def test_only_suffixes(self):
        assert normalize_merchant("PTE LTD") == ""

    def test_complex_transaction_string(self):
        assert normalize_merchant("STARBUCKS #12345 PTE LTD") == "starbucks"

    def test_grab_with_code(self):
        assert normalize_merchant("GRAB* A-4KXYZW") == "grab"

    def test_singapore_airlines(self):
        assert normalize_merchant("Singapore Airlines") == "singapore airlines"

    def test_ntuc_fairprice(self):
        assert normalize_merchant("NTUC FairPrice") == "ntuc fairprice"
