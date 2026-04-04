import argparse
import json
from pathlib import Path
from src.recommender import recommend


def run_single(merchant, hint, amount, cards):
    card_list = [c.strip() for c in cards.split(",")] if cards else None
    result = recommend(merchant, category_hint=hint, amount=amount, user_cards=card_list)
    print(json.dumps(result, indent=2))


def run_test():
    queries_path = Path(__file__).parent / "data" / "queries.json"
    with open(queries_path) as f:
        queries = json.load(f)

    for i, query in enumerate(queries):
        print(f"\n{'='*60}")
        print(f"Query {i+1}: {query['merchant']}")
        print(f"{'='*60}")

        result = recommend(
            merchant=query["merchant"],
            category_hint=query.get("category_hint"),
            amount=query["amount"],
            user_cards=query.get("user_cards"),
        )
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Card Spend AI Recommendation System")
    parser.add_argument("--merchant", type=str, help="Merchant name")
    parser.add_argument("--hint", type=str, help="Category hint (e.g. coffee, travel, shopping)")
    parser.add_argument("--amount", type=float, help="Transaction amount")
    parser.add_argument("--cards", type=str, help="Comma-separated list of card names")
    parser.add_argument("--test", action="store_true", help="Run all sample queries from queries.json")

    args = parser.parse_args()

    if args.test:
        run_test()
    elif args.merchant and args.amount is not None:
        run_single(args.merchant, args.hint, args.amount, args.cards)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
