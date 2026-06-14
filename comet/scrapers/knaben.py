from comet.core.logger import logger
from comet.scrapers.base import BaseScraper
from comet.scrapers.models import ScrapeRequest


class KnabenScraper(BaseScraper):
    """Knaben (knaben.org) — public torrent meta-aggregator, scraped natively via its JSON API.

    The community Prowlarr/Cardigann definition can search but its /download proxy 501s for many
    sources ("Fallback not implemented for: thepiratebay.org"), so those results get dropped. Here we
    POST to the v1 API and read magnetUrl + hash directly from each hit — no .torrent download, no
    501, no FlareSolverr. Cardigann can't do this (it form-encodes POST bodies); a native scraper can.
    """

    def __init__(self, manager, session, url: str):
        super().__init__(manager, session, url)

    async def scrape(self, request: ScrapeRequest):
        torrents = []
        try:
            body = {
                "search_type": "score",
                "search_field": "title",
                "query": request.title,
                "order_by": "seeders",
                "order_direction": "desc",
                "from": 0,
                "size": 300,
                "hide_unsafe": True,
                "hide_xxx": False,
            }
            response = await self.session.post(f"{self.url.rstrip('/')}/v1", json=body)
            data = await response.json()

            hits = data.get("hits", []) if isinstance(data, dict) else []
            for result in hits:
                info_hash = (result.get("hash") or "").strip().lower()
                if len(info_hash) not in (40, 32):
                    continue

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
        except Exception as e:
            logger.warning(
                f"Exception while getting torrents for {request.title} with Knaben ({self.url}): {e}"
            )

        return torrents
