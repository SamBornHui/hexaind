# Use the base Jupyter notebook image
FROM jupyter/base-notebook:latest

# Set up environment variables for pip cache directory
ENV PIP_CACHE_DIR=/var/cache/pip

# Switch to root user to install system dependencies
USER root

# Update the package lists and install necessary system dependencies
# Including libglib2.0-0 to resolve libgthread issues and libgl1-mesa-glx for OpenCV
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Switch to a non-root user to follow Jupyter's best practices
# USER ${NB_UID}

# Install Python dependencies from requirements.txt with pip caching enabled
RUN --mount=type=bind,source=jupyterhub/requirements.txt,target=requirements.txt \
    --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip install --no-cache-dir -r requirements.txt

