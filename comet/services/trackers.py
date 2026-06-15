import aiohttp

from comet.core.logger import logger

# Populated at startup from ngosang/trackerslist when DOWNLOAD_GENERIC_TRACKERS=True.
trackers = []

# Always-available baseline of reliable public trackers. Used as the fallback for hash-only torrents
# (e.g. Knaben / TheRARBG, which carry no announce URLs) so debrid can find peers and fetch metadata
# for an UNCACHED magnet — without trackers a bare infohash often can't be resolved ("unexpected
# provider response") and lands in the debrid account named by its hash. Works even if the larger
# downloaded list is disabled or the download failed.
DEFAULT_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://explodie.org:6969/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "http://tracker.openbittorrent.com:80/announce",
    "udp://tracker.dler.org:6969/announce",
    "udp://opentracker.i2p.rocks:6969/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://tracker1.bt.moack.co.kr:80/announce",
]


async def download_best_trackers():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
            ) as response:
                text = await response.text()

        trackers.clear()
        trackers.extend(line for line in text.split("\n") if line)
        logger.log(
            "COMET",
            f"Generic Trackers: downloaded {len(trackers)} trackers",
        )
    except Exception as e:
        logger.warning(f"Failed to download best trackers: {e}")
