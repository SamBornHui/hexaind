FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye

RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt update && \
    apt -y --no-install-recommends install \
        curl \
        gcc \
        libcairo2-dev \
        pkg-config \
        python3-dev
