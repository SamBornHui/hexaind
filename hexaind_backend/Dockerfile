# syntax=docker/dockerfile:1.7-labs
FROM python:3.10-slim AS base

# Set up Python virtual environment
RUN python -m venv /opt/venv

# Set environment variables for Python and pip
ENV PATH=/opt/venv/bin:${PATH} \
    PIP_CACHE_DIR=/var/cache/pip \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install required dependencies, including Wine
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
        curl \
        ffmpeg \
        gcc \
        libcairo2-dev \
        pkg-config \
        python3-dev \
        socat \
        wine64 \
        wine32 \
        winbind \
        xvfb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/local/src/hexaind_backend

FROM base AS prod

COPY --link --parents --exclude=*.egg-info openapi_clients/* .

# Install Python requirements for the production environment
RUN --mount=type=cache,id=backend-requirements,target=${PIP_CACHE_DIR},sharing=locked \
    --mount=type=bind,source=requirements.txt,target=requirements.txt,readonly \
    pip install --requirement requirements.txt

RUN rm -rf openapi_clients

# Copy source files
COPY --parents app/ tests/ integration_tests pyproject.toml README.md LICENSE ./

# Install project as an editable package
RUN pip install --editable . --no-deps

FROM base AS prod_ml

# Upgrade setuptools and wheel before installing ML requirements
RUN pip install --upgrade setuptools wheel
RUN pip install --use-pep517 seqeval

# Install Python requirements for the ML environment
RUN --mount=type=cache,id=backend-requirements,target=${PIP_CACHE_DIR},sharing=locked \
    --mount=type=bind,source=ml_requirements.txt,target=ml_requirements.txt,readonly \
    pip install --requirement ml_requirements.txt

# Copy source files
COPY --parents app/ tests/ integration_tests pyproject.toml README.md LICENSE ./

# Update Ray version and install project
RUN pip install ray==2.11.0
RUN pip install --editable . --no-deps
RUN apt-get update -y && apt-get install -y gcc && apt-get install -y git
