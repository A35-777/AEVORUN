"""Sample non-temporal code for false-positive validation."""

def quicksort(arr):
    """Standard quicksort algorithm with no temporal logic."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)


def string_word_frequency(text: str) -> dict:
    """Word frequency counter."""
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return counts

