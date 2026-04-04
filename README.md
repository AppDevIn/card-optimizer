# Card Spend AI Recommendation System

A prototype that recommends the best credit card for a given purchase. It resolves merchants through a multi-layer cascade (exact lookup, fuzzy matching, keyword inference, hint fallback) and ranks cards by reward rate, flagging low-confidence cases for review.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run all sample queries:

```bash
python main.py --test
```

Run a single query:

```bash
python main.py --merchant "Starbucks" --hint "coffee" --amount 12.50 --cards "Max Cashback+,Max Travel Visa"
```

Run tests:

```bash
python -m pytest tests/ -v
```

### CLI Flags

| Flag         | Required | Description                                                          |
| ------------ | -------- | -------------------------------------------------------------------- |
| `--merchant` | Yes      | Merchant name (e.g. "Starbucks", "Amazon SG")                        |
| `--amount`   | Yes      | Transaction amount in dollars                                        |
| `--hint`     | No       | Category hint (e.g. "coffee", "travel", "shopping")                  |
| `--cards`    | No       | Comma-separated card names. If omitted, shows top 3 across all cards |
| `--test`     | No       | Run all sample queries from `data/queries.json`                      |

## Assumptions

- **Category hint is optional and informal.** Users say "coffee" not "dining". The system tries exact lookup, fuzzy match, and keyword inference before falling back to the hint - a missing hint just removes one signal, it doesn't break anything.

- **Broad hints map to the best sub-category.** "Travel" could mean airlines, hotels, or travel portals. We check all sub-categories and pick whichever gives the best reward for the user's cards. We assume the user wants to maximize rewards, not that they're telling us the exact category.

- **Reward rates are percentages, not points/miles.** Real cards use points with variable redemption values (1 mile = 0.8-1.5 cents depending on how you redeem). We use flat percentages because the sample data is structured this way and modeling redemption requires user-specific preferences.

- **Confidence = recommendation certainty, not merchant identity certainty.** A fuzzy match at score 65 still gets `medium` because the category comes from our database. The name match is approximate but the reward rate is based on verified data.

- **Small dataset, fits in memory.** 7 merchants, 4 cards - no database needed. At production scale we'd need indexed lookup.

- **One category per merchant.** Amazon sells groceries, electronics, and clothing - each with different reward rates. We don't model this because the sample data doesn't require it, but it matters in production.

- **No spending caps or monthly limits.** Real cards cap rewards (e.g. "5% on dining up to $500/month"). We ignore this since the sample data doesn't include caps, but we flag close-call situations where caps could flip the recommendation.

- **ASCII-friendly transaction strings.** Preprocessing handles store IDs, corporate suffixes, and punctuation but assumes Latin characters. CJK or diacritics would need additional normalization.

## Tradeoffs

**Keyword matching over sentence-transformers.** Sentence-transformers would give semantic understanding ("Blue Bottle Coffee" → dining) but adds ~2GB of dependencies, 5-10s cold start, and a model that's hard to debug. Keyword matching is transparent - you can read `category_descriptors.json` and see exactly what maps where. It fails on names with no descriptor words (like "Don Don Donki"), but that's what hint fallback handles. The cascade architecture is designed so sentence-transformers could slot in as a new layer later without changing anything else.

**No LLM for explanations.** Template-based explanations are deterministic, instant, and testable. An LLM adds latency, rate limits, non-determinism, and a hard-to-test dependency. For a recommendation engine where trust matters, deterministic is the right default. LLM explanations make sense as an optional enhancement, not the core path.

**Flat JSON over a database.** No concurrent writes, no indexing but also no setup, no migrations, and anyone can inspect the data with a text editor. The update queue uses JSONL (one object per line) so it's append-safe and easy to grep through.

**RapidFuzz WRatio with 60/80 thresholds.** WRatio handles partial names ("Amazon SG" vs "Amazon"), reordering, and abbreviations better than simpler scorers. 60-79 accepts but flags for review; 80+ accepts cleanly. Validated against sample data: "Amazon SG" scores 90 (correct accept), "Don Don Donki" scores below 60 against all merchants (correct rejection). Risk: false positives in the 60-79 band at larger scale, mitigated by human review.

**20% close-call threshold.** When two cards are within 20%, the "best" depends on factors we don't model: spending caps, sign-up bonuses, annual fees. We flag these rather than picking confidently. Errs toward surfacing uncertainty - a false flag beats a confidently wrong recommendation.

**Category groups for hint resolution.** 4 hand-curated groups (travel, food, shopping, transport). Works for prototype scope but won't scale every new category needs manual assignment. Embedding-based similarity would handle novel categories automatically but adds heavy dependencies.

**Cascade with short-circuit.** Each layer resolves the merchant; success skips remaining layers. Simpler to reason about, faster, and avoids conflicting signals between layers. Downside: if exact lookup matches, we can't detect potential miscategorizations in our own DB except through the hint mismatch check.

## AI Usage

I used Claude Code as a brainstorming and research partner throughout the project. I discussed architecture options, explored fuzzy matching approaches (comparing RapidFuzz scorers and thresholds), and iterated on edge case handling before writing code. The design decisions the cascade architecture, confidence model, threshold values came out of that back-and-forth. AI was used to write test cases.
