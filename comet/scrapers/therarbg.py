from urllib.parse import quote

from comet.core.logger import logger
from comet.scrapers.base import BaseScraper
from comet.scrapers.models import ScrapeRequest

# Air Disasters returned total=65 at page_size=50; 3 pages (~150) covers even busy titles without
# hammering the site, and Comet caps results per resolution downstream anyway.
THERARBG_MAX_PAGES = 3


class TherarbgScraper(BaseScraper):
    """TheRARBG (therarbg.to) — public RARBG-successor with a clean GET JSON API.

    /get-posts/keywords:{q}/?format=json returns a results[] array where each row carries the
    infohash ("h") directly, so Comet never fetches a .torrent through FlareSolverr/Byparr. The
    API is not Cloudflare-gated, so plain requests work (no impersonation needed).
    """

    def __init__(self, manager, session, url: str):
        super().__init__(manager, session, url)

    async def scrape(self, request: ScrapeRequest):
        torrents = []
        base = self.url.rstrip("/")
        seen = set()
        # Search the canonical title AND alternate/regional titles (Mayday, Air Crash Investigation,
        # ...) so #DUPE# shows whose torrents use a different name get pulled in. seen dedups across.
        for query in [request.title, *request.aliases]:
            if not query:
                continue
            try:
                url = f"{base}/get-posts/keywords:{quote(query)}/?format=json"
                pages = 0
                while url and pages < THERARBG_MAX_PAGES:
                    response = await self.session.get(url)
                    data = await response.json()
                    pages += 1

                    for result in data.get("results", []):
                        info_hash = (result.get("h") or "").strip().lower()
                        if len(info_hash) not in (40, 32) or info_hash in seen:
                            continue
                        seen.add(info_hash)

                        size = result.get("s")
                        seeders = result.get("se")
                        uploader = result.get("u") or "TheRARBG"

                        torrents.append(
                            {
                                "title": result.get("n"),
                                "infoHash": info_hash,
                                "fileIndex": None,
                                "seeders": int(seeders) if seeders is not None else None,
                                "size": int(size) if size is not None else None,
                                "tracker": f"TheRARBG | {uploader}",
                                "sources": [],
                            }
                        )

                    url = (data.get("links") or {}).get("next")
            except Exception as e:
                logger.warning(
                    f"Exception while getting torrents for {query} with TheRARBG ({self.url}): {e}"
                )

        return torrents
