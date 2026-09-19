# Configuration file for JupyterHub
import os
import sys
from dockerspawner import DockerSpawner

class CustomDockerSwapner(DockerSpawner):
    def start(self):
        user_options = self._trait_values.get("user_options", {})

        if "memory_limit" in user_options:
            self.mem_limit = user_options["memory_limit"]
            self.environment.update({"USER_MEMORY_LIMIT": self.mem_limit})
        if "cpu_limit" in user_options:
            self.cpu_limit = float(user_options["cpu_limit"])
            self.environment.update({"USER_CPU_LIMIT": self.cpu_limit})
        if "volumes" in user_options:
            self.volumes = user_options["volumes"]
            self.environment.update({"USER_VOLUMES": ", ".join(self.volumes.keys())})
        if "mounts" in user_options:
            self.mounts = user_options["mounts"]
            self.volumes = {}
            self.environment.update({"USER_MOUNTS": repr(self.mounts), "USER_VOLUMES": ""})
        if "notebook_image" in user_options:
            self.image = user_options["notebook_image"]
            self.environment.update({"USER_IMAGE": self.image})
        if "notebook_dir" in user_options:
            self.notebook_dir = user_options["notebook_dir"]
            self.environment.update({"USER_NOTEBOOK_DIR": self.notebook_dir})
        if "environment" in user_options:
            self.environment.update(user_options["environment"])

        return super().start()

c = get_config()  # noqa: F821

# We rely on environment variables to configure JupyterHub so that we
# avoid having to rebuild the JupyterHub container every time we change a
# configuration parameter.

# Spawn single-user servers as Docker containers
c.JupyterHub.spawner_class = CustomDockerSwapner

# Spawn containers from this image
c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]

c.DockerSpawner.environment = {
    "NATIVE_HOST": os.environ.get("NATIVE_HOST"),   
}

# Connect containers to this Docker network
network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name

# Explicitly set notebook directory because we'll be mounting a volume to it.
# Most `jupyter/docker-stacks` *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")


host_jupyterhub_path = os.environ.get("HOST_JUPYTERHUB_WORK_DIR") + "/p_{username}"
hexaind_jupyterhub_path = os.environ.get("HEXAIND_DATA_JUPYTERHUB_WORK_DIR") + "/p_{username}"

# override hexaind_jupyterhub_path to make previous files work
# post complete migration we can remove jupyterhub-user-{username} mount
# and replace destination of host_jupyterhub_path mount
# till we store these paths in DB changing paths internal to container anyway doesn't cause issues

parent_notebook_dir = os.path.dirname(os.path.abspath(notebook_dir))
hexaind_data = os.getenv("HEXAIND_DATA")

c.DockerSpawner.notebook_dir = parent_notebook_dir

# c.DockerSpawner.extra_create_kwargs = {"user": "root"}


# Mount the real user's Docker volume on the host to the notebook user's
# notebook directory in the container
c.DockerSpawner.volumes = {
    "jupyterhub-user-{username}": notebook_dir,
    host_jupyterhub_path: {"bind": parent_notebook_dir + "/p_{username}", "mode": "rw"},
    "hexaind-data":hexaind_data
}


# Remove containers once they are stopped
c.DockerSpawner.remove = True

# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = "jupyterhub"
c.JupyterHub.hub_port = 8080
c.JupyterHub.public_url = os.environ["JUPYTERHUB_PUBLIC_URL"]

# Persist hub data on volume mounted inside container
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"
c.JupyterHub.allow_named_servers = True

# Authenticate users with Native Authenticator
c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"

# # Allow anyone to sign-up without approval
# c.NativeAuthenticator.open_signup = True

c.DummyAuthenticator.password = os.environ.get("JUPYTERHUB_ADMIN")

# Allowed admins
admin = os.environ.get("JUPYTERHUB_ADMIN")
if admin:
    c.Authenticator.admin_users = [admin]

# Allowed ahead-of-time admin tokens
admin_token = os.environ.get("JUPYTERHUB_API_TOKEN")
if admin_token and admin:
    c.JupyterHub.api_tokens = {admin_token: admin}

# limiting concurrent server by user
def named_server_limit_per_user_fn(handler):
    user = handler.current_user
    if user and user.admin:
        return 0
    return 1

c.JupyterHub.named_server_limit_per_user = named_server_limit_per_user_fn

c.ServerApp.shutdown_no_activity_timeout = 30 * 60
c.MappingKernelManager.cull_idle_timeout = 30 * 60
c.MappingKernelManager.cull_interval = 1 * 60
c.MappingKernelManager.cull_connected = True

c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'admin': True,
        'command': [sys.executable, '-m', 'jupyterhub_idle_culler', '--timeout=1800']
    }
]
