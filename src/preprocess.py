import re

CORPORATE_SUFFIXES = {"pte", "ltd", "llc", "inc", "corp", "sdn", "bhd", "co", "pty"}


def normalize_merchant(name):
    if not name:
        return ""

    text = name.lower()

    text = re.sub(r'[#*]\s*\S+', '', text)

    words = text.split()
    words = [w for w in words if w not in CORPORATE_SUFFIXES]
    text = " ".join(words)

    text = re.sub(r'[^\w\s]', '', text)

    text = re.sub(r'\s+', ' ', text).strip()

    return text
