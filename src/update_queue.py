import json
from datetime import datetime, timezone
from src.categories import DATA_DIR

QUEUE_FILE = DATA_DIR / "update_queue.jsonl"


def append_update(merchant, update_info, match_type, inferred_category):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant": merchant,
        "type": update_info["type"],
        "inferred_category": inferred_category,
        "match_type": match_type,
        "reason": update_info["reason"],
    }

    if "matched_to" in update_info:
        entry["matched_to"] = update_info["matched_to"]
    if "score" in update_info:
        entry["score"] = update_info["score"]

    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
