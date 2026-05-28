# JupyterHub itself: hub + configurable-http-proxy + DockerSpawner + NativeAuthenticator.
FROM quay.io/jupyterhub/jupyterhub:5

RUN python3 -m pip install --no-cache-dir \
      dockerspawner \
      pyjwt

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY labauth.py /srv/jupyterhub/labauth.py
WORKDIR /srv/jupyterhub
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
