from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SearchParams:
    season: Optional[int]
    episode: Optional[int]


def normalize_search_params(
    season: Optional[int],
    episode: Optional[int],
    search_season: Optional[int] = None,
    search_episode: Optional[int] = None,
) -> SearchParams:
    return SearchParams(
        season=search_season if search_season is not None else season,
        episode=search_episode if search_episode is not None else episode,
    )


def build_torrent_cache_where(
    media_id: str,
    season: Optional[int],
    episode: Optional[int],
    aggregate: bool = False,
) -> tuple[str, dict]:
    where_clause = """
        FROM torrents
        WHERE media_id = :media_id
    """
    params = {"media_id": media_id}
    if season is not None:
        where_clause += """
        AND season = CAST(:season as INTEGER)
        """
        params["season"] = season
    # Scope search (Season/Series buttons null the episode). Aggregate EVERYTHING in scope —
    # individual episodes AND packs — so skip the episode restriction entirely. The season filter
    # above already narrows "season" scope; "series" scope (season also None) returns the whole show.
    # Without this, episode=None collapses the clause to `episode IS NULL` = packs only, which is
    # ~empty for shows released purely as single episodes (e.g. Air Disasters).
    if not (aggregate and episode is None):
        where_clause += """
        AND (episode IS NULL OR episode = CAST(:episode as INTEGER))
        """
        params["episode"] = episode
    return where_clause, params
