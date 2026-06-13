"""
Recover the real title of a Cinemeta "#DUPE#" series from TheTVDB — keylessly.

Cinemeta de-duplicates shows that have multiple regional IMDb entries (e.g. Mayday / Air Crash
Investigation / Air Disasters): it renames the duplicate's `name` to the literal "#DUPE#"
(slug "<type>/dupe-<canonicalId>") and the duplicate's own IMDb id is dead/merged upstream. So
id-based metadata (IMDb suggestion, Cinemeta fallback) yields either "#DUPE#" or the *canonical*
title — and the scraper then searches the wrong thing (e.g. Comet searches "Mayday" for an
"Air Disasters" request, returning mis-numbered episodes).

The dupe's Cinemeta meta still carries a `tvdb_id`, which maps to the correct regional entry on
TheTVDB. We hit the by-id "dereferrer" (302 → series page) and read the page <title> ("<Name> -
TheTVDB.com") plus its "Aliases" block. No API key required.

This is generic: any `#DUPE#` glitch is handled, not a hard-coded show.
"""

import re

import aiohttp

from comet.core.logger import logger

_CINEMETA_META_URL = "https://v3-cinemeta.strem.io/meta/series/{id}.json"
_TVDB_DEREFERRER = "https://thetvdb.com/dereferrer/series/{tvdb_id}"
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_TITLE_RE = re.compile(r"<title>\s*(.*?)\s*-\s*TheTVDB\.com\s*</title>", re.IGNORECASE | re.DOTALL)
_FIRST_AIRED_RE = re.compile(
    r"First Aired\s*</strong>\s*<span>\s*<a[^>]*>\s*([^<]+?)\s*</a>", re.IGNORECASE
)
_ALIASES_BLOCK_RE = re.compile(r"Aliases([\s\S]{0,600})", re.IGNORECASE)
_LI_RE = re.compile(r"<li[^>]*>\s*([^<]+?)\s*</li>")
_YEAR_RE = re.compile(r"(\d{4})")


def _is_dupe(meta: dict) -> bool:
    if (meta.get("name") or "").strip() == "#DUPE#":
        return True
    slug = (meta.get("slug") or "").lower().strip()
    return slug.startswith(("series/dupe-", "movie/dupe-", "dupe-"))


async def get_tvdb_dupe_metadata(session: aiohttp.ClientSession, imdb_id: str):
    """
    If `imdb_id` is a Cinemeta "#DUPE#" entry with a tvdb_id, return
    ``(title, aliases: list[str], year: int | None)`` resolved from TheTVDB; otherwise ``None``.
    """
    if not imdb_id or not imdb_id.startswith("tt"):
        return None

    # 1) Is this id a dupe, and does it carry a tvdb_id?
    try:
        async with session.get(_CINEMETA_META_URL.format(id=imdb_id)) as response:
            if response.status != 200:
                return None
            meta = (await response.json()).get("meta") or {}
    except Exception:
        return None

    if not _is_dupe(meta):
        return None

    tvdb_id = meta.get("tvdb_id")
    if not tvdb_id:
        return None

    # 2) Resolve the real title + aliases + year from TheTVDB (keyless).
    try:
        async with session.get(
            _TVDB_DEREFERRER.format(tvdb_id=tvdb_id), headers={"User-Agent": _UA}
        ) as response:
            if response.status != 200:
                return None
            html = await response.text()
    except Exception:
        return None

    title_match = _TITLE_RE.search(html)
    title = title_match.group(1).strip() if title_match else None
    if not title or title == "#DUPE#":
        return None

    aliases = []
    block = _ALIASES_BLOCK_RE.search(html)
    if block:
        aliases = [
            a.strip()
            for a in _LI_RE.findall(block.group(1))
            if a.strip() and a.strip().lower() != title.lower()
        ][:8]

    year = None
    aired = _FIRST_AIRED_RE.search(html)
    if aired:
        ymatch = _YEAR_RE.search(aired.group(1))
        if ymatch:
            year = int(ymatch.group(1))

    logger.log(
        "SCRAPER",
        f"🩹 TheTVDB dupe fix: {imdb_id} → '{title}'"
        + (f" (+{len(aliases)} aliases)" if aliases else ""),
    )
    return title, aliases, year
