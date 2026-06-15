from comet.core.logger import logger
from comet.scrapers.base import BaseScraper
from comet.scrapers.models import ScrapeRequest

# Knaben caps a response page; pull a few pages (by seeders) so deep catalogues like "Mayday" (~669
# matches) aren't truncated to the single most-seeded page. Comet caps results per resolution later.
KNABEN_PAGE_SIZE = 300
KNABEN_MAX_PAGES = 3


class KnabenScraper(BaseScraper):
    """Knaben (knaben.org) — public torrent meta-aggregator, scraped natively via its JSON API.

    The community Prowlarr/Cardigann definition can search but its /download proxy 501s for many
    sources ("Fallback not implemented for: thepiratebay.org"), so those results get dropped. Here we
    POST to the v1 API and read magnetUrl + hash directly from each hit — no .torrent download, no
    501, no FlareSolverr. Cardigann can't do this (it form-encodes POST bodies); a native scraper can.

    search_type MUST be "100%" (every query term present in the title). The "score" mode is a loose
    relevance match that, combined with order_by=seeders, returns the site's top-seeded torrents
    (software cracks, popular anime) instead of title matches — i.e. pure noise. "100%" makes
    "air disasters" return Air Disasters / Air Crash Investigation episodes, "mayday" return Mayday
    episodes, etc.
    """

    def __init__(self, manager, session, url: str):
        super().__init__(manager, session, url)

    async def scrape(self, request: ScrapeRequest):
        torrents = []
        seen_hashes = set()
        endpoint = f"{self.url.rstrip('/')}/v1"

        # Search the canonical title AND any alternate/regional titles (Mayday, Air Crash
        # Investigation, ...) so #DUPE# shows whose torrents use a different name get pulled in.
        for query in [request.title, *request.aliases]:
            if not query:
                continue
            try:
                for page in range(KNABEN_MAX_PAGES):
                    body = {
                        "search_type": "100%",
                        "search_field": "title",
                        "query": query,
                        "order_by": "seeders",
                        "order_direction": "desc",
                        "from": page * KNABEN_PAGE_SIZE,
                        "size": KNABEN_PAGE_SIZE,
                        "hide_unsafe": True,
                        "hide_xxx": False,
                    }
                    response = await self.session.post(endpoint, json=body)
                    data = await response.json()

                    hits = data.get("hits", []) if isinstance(data, dict) else []
                    if not hits:
                        break

                    for result in hits:
                        info_hash = (result.get("hash") or "").strip().lower()
                        if len(info_hash) not in (40, 32) or info_hash in seen_hashes:
                            continue
                        seen_hashes.add(info_hash)

                        size = result.get("bytes")
                        seeders = result.get("seeders")
                        sub_tracker = result.get("tracker") or "Knaben"

                        torrents.append(
                            {
                                "title": result.get("title"),
                                "infoHash": info_hash,
                                "fileIndex": None,
                                "seeders": int(seeders) if seeders is not None else None,
                                "size": int(size) if size is not None else None,
                                "tracker": f"Knaben | {sub_tracker}",
                                "sources": [],
                            }
                        )

                    # Last page reached (Knaben returned a short page).
                    if len(hits) < KNABEN_PAGE_SIZE:
                        break
            except Exception as e:
                logger.warning(
                    f"Exception while getting torrents for {query} with Knaben ({self.url}): {e}"
                )

        return torrents
