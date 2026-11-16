"""Normalise phone numbers that arrived through speech recognition."""

import re

DIGITS = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9",
}


def normalize_phone(value: str) -> str | None:
    """Return ten Indian mobile digits, or None when the input is invalid."""
    if not isinstance(value, str):
        return None
    text = value.lower().strip()
    output: list[str] = []
    tokens = re.findall(r"[a-z]+|\d+", text)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"double", "triple"} and index + 1 < len(tokens):
            repeated = DIGITS.get(tokens[index + 1], tokens[index + 1] if tokens[index + 1].isdigit() else "")
            if repeated:
                output.append(repeated * (2 if token == "double" else 3))
                index += 2
                continue
        if token in DIGITS:
            output.append(DIGITS[token])
        elif token.isdigit():
            output.append(token)
        index += 1

    digits = "".join(output)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) != 10 or digits[0] not in "6789":
        return None
    return digits


def format_phone_for_speech(phone: str) -> str:
    """Format digits so a voice agent can read them back clearly."""
    return " ".join((phone[:5], phone[5:]))
