import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

CATEGORY_GROUPS = {
    "travel": ["airlines", "hotels", "travel_portal"],
    "food": ["dining", "groceries"],
    "shopping": ["online_shopping"],
    "transport": ["transport"],
}

GROUP_LOOKUP = {}
for group, categories in CATEGORY_GROUPS.items():
    for cat in categories:
        GROUP_LOOKUP[cat] = group


def load_category_aliases():
    with open(DATA_DIR / "category_aliases.json") as f:
        return json.load(f)


def load_category_descriptors():
    with open(DATA_DIR / "category_descriptors.json") as f:
        return json.load(f)


def resolve_hint(hint, aliases=None):
    if not hint:
        return None

    hint = hint.lower().strip()

    if aliases is None:
        aliases = load_category_aliases()

    if hint in aliases:
        return aliases[hint]

    all_categories = set()
    for cats in CATEGORY_GROUPS.values():
        all_categories.update(cats)
    all_categories.add("general")

    if hint in all_categories:
        return hint

    if hint in CATEGORY_GROUPS:
        return CATEGORY_GROUPS[hint]

    return None


def categories_in_same_group(cat1, cat2):
    if cat1 == cat2:
        return True
    return GROUP_LOOKUP.get(cat1) == GROUP_LOOKUP.get(cat2) and GROUP_LOOKUP.get(cat1) is not None
