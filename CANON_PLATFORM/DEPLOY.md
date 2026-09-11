# Deploying CANON Platform to a shareable public URL

This app is a **Python server** (FastAPI). GitHub **Pages cannot host it** (Pages = static
files only). Use a container host. All three below give you a public URL and are free-tier.

The app is now **self-contained** — the TK-401 seed is bundled in `seed/`, and the 100-machine
library is in `samples/library/`. No sibling folders needed.

> Note on the brain: a cloud deploy runs in **deterministic mode** (still real + safe) unless
> you expose the trained model endpoint publicly and set `CANON_LLM_BASE`. Don't expose a raw
> model to the internet without auth. For the brain demo, run locally with the SSH tunnel.

## Option A — Hugging Face Spaces (easiest free URL)
1. Create a new **Space** → SDK: **Docker**.
2. Push the contents of this `CANON_PLATFORM/` folder to the Space repo.
3. Add this frontmatter to the Space's `README.md` (or rename `SPACE_README.md`):
   ```
   ---
   title: CANON Platform
   sdk: docker
   app_port: 7860
   ---
   ```
4. The Space builds the `Dockerfile` and serves at `https://<user>-canon-platform.hf.space`.

## Option B — Render.com
1. New → **Web Service** → connect the repo (root = this folder).
2. Environment: **Docker** (it uses the `Dockerfile`). Render injects `$PORT` (app.py reads it).
3. Deploy → public URL `https://canon-platform.onrender.com`.

## Option C — Railway / Fly.io
- **Railway**: New Project → Deploy from repo → it detects the Dockerfile → public domain.
- **Fly.io**: `fly launch` in this folder (uses the Dockerfile) → `fly deploy`.

## Local container test first
```bash
cd .context/CANON_PLATFORM
docker build -t canon-platform .
docker run -p 7860:7860 canon-platform
# open http://localhost:7860
```

## The static CANON app (different thing) → GitHub Pages
`../CANON/index.html` is a static single-file app (deterministic compiler demo) and *can* go on
GitHub Pages. That is NOT this platform — it has no upload/brain/simulator server.
