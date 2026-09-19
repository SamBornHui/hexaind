ARG JUPYTERHUB_VERSION
FROM jupyterhub/jupyterhub:latest

RUN python3 -m pip install --no-cache-dir \
        dockerspawner \
        jupyterhub-nativeauthenticator \
        jupyterhub-idle-culler
CMD ["jupyterhub", "-f", "/srv/jupyterhub/config.py"]