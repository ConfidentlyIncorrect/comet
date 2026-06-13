# Self-hosted Comet (patched) — name-search torrent addon for Nuvio

This is a fork of [g0ldyy/comet](https://github.com/g0ldyy/comet) with one addition: a **generic
TheTVDB `#DUPE#` fix**. Cinemeta de-duplicates regional shows (Mayday / Air Crash Investigation /
**Air Disasters**) into a dead `#DUPE#` id; id-based addons then search the *wrong* title. Comet now
detects that and resolves the real title + aliases from TheTVDB, so the search isn't poisoned.

- Patch: `comet/metadata/tvdb_dupe.py` + the override in `comet/metadata/manager.py`.
- It's keyless and generic — every `#DUPE#` glitch is handled, not a hard-coded show.

## Stack
`Comet` (built from this repo, patch baked in) → `Prowlarr` (indexers; 1337x etc. via
`FlareSolverr` for Cloudflare) → `Postgres`. Plus the free built-in scrapers (Zilean/DMM, Torrentio,
StremThru) enabled by default. Light enough to sit beside the DaddyLive stack (~1 GB RAM).

## Bring-up

```bash
cd deployment/selfhost
cp .env.example .env            # edit TZ if you like; leave PROWLARR_API_KEY blank for now
docker compose --env-file .env up -d --build
```

### One-time Prowlarr setup
1. Open **http://<vps>:9696** → Settings → General → copy the **API Key**.
2. Put it in `.env` as `PROWLARR_API_KEY=...`.
3. **FlareSolverr** (for Cloudflare-walled indexers like 1337x): Settings → Indexers → **Add Proxy**
   → FlareSolverr → Host `http://flaresolverr:8191` → give it a Tag (e.g. `flaresolverr`).
4. **Add indexers**: Indexers → Add → e.g. **1337x**, **The Pirate Bay**, **TorrentGalaxy**, etc.
   For Cloudflare ones (1337x), set their **Proxy** tag to `flaresolverr`.
5. Re-apply the API key to Comet:
   ```bash
   docker compose --env-file .env up -d
   ```

### Install in Nuvio
1. Open **http://<vps>:8000** → configure your **debrid** (AllDebrid key and/or TorBox key) + options
   → it gives you an install URL like `http://<vps>:8000/<config>/manifest.json`.
2. Add that URL as an addon in Nuvio.
3. Open **Air Disasters** → an episode → you should now get the full catalogue of correctly-titled
   torrents (look for the `🩹 TheTVDB dupe fix` line in `docker compose logs comet`).

## Notes
- Comet self-aggregates (Prowlarr + Zilean/DMM + Torrentio + StremThru), so you do **not** need
  AIOStreams. It exposes one standard addon URL, which Nuvio handles natively.
- Comet's port `8000` must be reachable by your TV box (same as how DaddyLive is exposed).
- Upstream updates: `git fetch upstream && git merge upstream/main` then `up -d --build` (the patch
  is isolated to `comet/metadata/`, so conflicts should be minimal).
