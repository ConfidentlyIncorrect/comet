from typing import List, Optional, TypedDict

from pydantic import BaseModel


class ScrapeRequest(BaseModel):
    media_type: str  # "movie" or "series"
    media_id: str  # Full ID (e.g., "tt1234567:1:1" or "kitsu:123")
    media_only_id: str  # Base ID (e.g., "tt1234567")
    title: str
    # Extra search terms — alternate/regional titles the show is released under (the alias "ez"
    # bucket: canonical + TheTVDB aliases). Crucial for #DUPE# shows whose torrents use a DIFFERENT
    # name than the title, e.g. "Air Disasters" is on torrents as "Mayday" / "Air Crash
    # Investigation". Name-based scrapers search title + these; the result filter already accepts
    # them because the same aliases live in the filter alias dict. Capped by SEARCH_ALIAS_LIMIT.
    aliases: List[str] = []
    year: Optional[int] = None
    year_end: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    context: str = "live"  # "live" or "background"


class ScrapeResult(TypedDict):
    title: str
    infoHash: str
    fileIndex: Optional[int]
    seeders: Optional[int]
    size: Optional[int]
    tracker: str
    sources: List[str]
