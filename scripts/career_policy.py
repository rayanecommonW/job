"""Shared screening rules for career queues and document staging."""
import re


def staff_only(title):
    """Staff-only titles are excluded; explicit Senior/Staff alternatives are allowed."""
    combined = r'\b(?:senior|sr\.?)\s*(?:/|or|and|&|\|)\s*staff\b|\bstaff\s*(?:/|or|and|&|\|)\s*(?:senior|sr\.?)\b'
    return bool(re.search(r'\bstaff\b', title, re.I) and not re.search(combined, title, re.I))


def requires_staff(title, posting=''):
    """Catch explicit Staff requirements hidden behind a generic posting title."""
    if staff_only(title):
        return True
    if re.search(r'\bstaff\b', title, re.I):
        return False  # An explicit Senior/Staff alternative is eligible.
    return bool(re.search(
        r'\bas (?:a|the) staff(?:[- ]level)? (?:\w+\s+){0,3}engineer\b'
        r'|\bstaff[- ]level experience\b', posting, re.I))
