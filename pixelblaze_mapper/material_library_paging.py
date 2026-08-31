"""Pure paging helpers for the MadMapper material-library browser."""

from __future__ import annotations


def page_count(item_count: int, page_size: int) -> int:
    """Return at least one page and reject invalid paging inputs."""

    count = int(item_count)
    size = int(page_size)
    if count < 0:
        raise ValueError("item_count must not be negative")
    if size <= 0:
        raise ValueError("page_size must be positive")
    return max(1, (count + size - 1) // size)


def clamped_page(
    current_page: int,
    delta: int,
    item_count: int,
    page_size: int,
) -> tuple[int, int]:
    """Return ``(page, count)`` after applying a bounded page delta."""

    count = page_count(item_count, page_size)
    page = max(0, min(count - 1, int(current_page) + int(delta)))
    return page, count


__all__ = ["clamped_page", "page_count"]
