# jupyterhub-capstone

Dockerized **JupyterHub** for CodePath KSA capstone projects — a full JupyterLab where students
assemble everything (real LangChain, multi-step, exploratory). Bite-sized lessons run in-app on
Judge0 / the agent-runner; the open capstone runs here.

## Architecture
- **DockerSpawner** — each student gets their own isolated container (they run arbitrary code).
- **NativeAuthenticator** — students self-register; an admin approves (no open self-serve).
- **Single-user image** `capstone-notebook` = `scipy-notebook` + `langchain`/`langchain-openai`/`langgraph`.
  Built on the box by the `notebook-image` one-shot service (no registry needed).
- Per-user **mem/cpu limits** + per-user persistent volume (`/home/jovyan/work`).
- Students bring **their own LLM keys** (set in their notebook env) — nothing server-side to leak.

## Deploy (Docker Manager API, build-on-VPS)
Deployed as the `jupyterhub` Dockge stack. Required env:
- `ADMIN_USERS` — comma-sep admin usernames (e.g. `admin`).
- `HUB_API_TOKEN` — random hex; admin REST token for checks/future app integration.
- `MEM_LIMIT` / `CPU_LIMIT` — per-student caps (default `1G` / `1.0`).

First spawn builds/uses `capstone-notebook:latest` locally (`pull_policy=ifnotpresent`).

## Reaching it
For now: `http://<vps-ip>:8000` (HTTP — fine for setup, **not** for real student logins).
Production: point `hub.<domain>` at the box and route through the existing Traefik
(`websecure` + `letsencrypt`) so logins are over TLS.

## Security notes
- The hub mounts the **docker socket** (DockerSpawner needs it) — socket access ≈ host root.
  Strong admin auth + TLS are required before exposing to students.
- Each student container is mem/cpu-capped; add an **idle-culler** to reclaim RAM (fast-follow).
- Box is shared with Judge0 — ~7 GB RAM free, so keep per-user limits + culling on.
