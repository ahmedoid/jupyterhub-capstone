import os

c = get_config()  # noqa

# ── Spawner: each student gets their OWN container (isolation) ──────────────
# Students run arbitrary code, so never share a process space.
c.JupyterHub.spawner_class = "docker"
c.DockerSpawner.image = os.environ.get("DOCKER_NOTEBOOK_IMAGE", "capstone-notebook:latest")
# Use the local image built by the stack (don't try to pull it from a registry).
c.DockerSpawner.pull_policy = os.environ.get("PULL_POLICY", "ifnotpresent")
# Spawned containers join the stack network so they can reach the hub.
c.DockerSpawner.network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.remove = True  # tear down the container when the server stops
# Resource caps per student (the box is shared with Judge0 — keep it bounded).
c.DockerSpawner.mem_limit = os.environ.get("MEM_LIMIT", "1G")
c.DockerSpawner.cpu_limit = float(os.environ.get("CPU_LIMIT", "1.0"))
# Persist each student's notebooks across restarts (named volume per user).
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": "/home/jovyan/work"}
c.DockerSpawner.notebook_dir = "/home/jovyan/work"

# ── Hub reachability from the spawned containers ───────────────────────────
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = os.environ.get("HUB_CONNECT_IP", "jupyterhub")
c.JupyterHub.port = 8000

# Behind a TLS reverse proxy (Traefik) — tell the hub its external URL so OAuth/login
# redirects use https://lab.bytek.tech instead of the internal http://...:8000.
_pub = os.environ.get("PUBLIC_URL")
if _pub:
    c.JupyterHub.public_url = _pub

# ── Auth: SSO via launch token from the app (no login form) ────────────────
import sys as _sys
_sys.path.insert(0, "/srv/jupyterhub")
from labauth import username_from_email as _slug  # noqa: E402

c.JupyterHub.authenticator_class = "labauth.LabAuthenticator"
# Admins listed by email; stored usernames are the email slug, so slug them too.
c.Authenticator.admin_users = {_slug(x) for x in os.environ.get("ADMIN_USERS", "").split(",") if x.strip()}
c.Authenticator.allow_all = True  # JupyterHub 5 defaults to deny-all; identity is trusted via the token

# ── Persist hub state on a named volume ────────────────────────────────────
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/jupyterhub.sqlite"
c.JupyterHub.cookie_secret_file = "/srv/jupyterhub/cookie_secret"

# ── Services + roles ───────────────────────────────────────────────────────
_services = []
_roles = []

# Optional admin API token (for programmatic checks / app integration).
_tok = os.environ.get("HUB_API_TOKEN")
if _tok:
    _services.append({"name": "admin-api", "api_token": _tok})
    _roles.append({
        "name": "admin-api-role",
        "scopes": ["admin:users", "admin:servers", "read:hub"],
        "services": ["admin-api"],
    })

# Idle-culler: stop a student's container after it's idle for a while, to reclaim RAM
# (the box is shared with Judge0). Timeout configurable via CULL_TIMEOUT (default 3600s).
_cull = int(os.environ.get("CULL_TIMEOUT", "3600"))
_services.append({
    "name": "idle-culler",
    "command": ["python3", "-m", "jupyterhub_idle_culler", f"--timeout={_cull}"],
})
_roles.append({
    "name": "idle-culler",
    "scopes": ["list:users", "read:users:activity", "read:servers", "delete:servers"],
    "services": ["idle-culler"],
})

c.JupyterHub.services = _services
c.JupyterHub.load_roles = _roles
