import requests
import logging
from typing import Dict, List, Optional, Any, Union, Literal
from urllib.parse import urljoin
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AppInfo(BaseModel):
    """Pydantic model for application information."""
    name: str = Field(..., description="Name of the application")
    url: str = Field(..., description="URL of the application in Argo CD UI")
    ingress_url: Optional[str] = Field(None, description="Ingress URL for the application if available")
    health_status: Optional[str] = Field(None, description="Health status of the application")

class AppHubService:
    """Service to interact with Argo CD API using direct REST calls."""
    
    def __init__(
        self, 
        host: str = "https://hexaind-op-sage1-apphub.corp.databrick.tech",
        username: str = "admin",
        password: str = "changeme"
    ) -> None:
        """
        Initialize the Argo CD service.
        
        Args:
            host: The Argo CD server host URL
            username: The username for authentication
            password: The password for authentication
        """
        self.host = host
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        # Disable SSL verification if needed (for self-signed certificates)
        # self.session.verify = False
    
    def login(self) -> None:
        """
        Login to Argo CD and get authentication token.
        
        Raises:
            Exception: If login fails
        """
        try:
            login_url = urljoin(self.host, "/api/v1/session")
            login_payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(login_url, json=login_payload, timeout=3)
            response.raise_for_status()
            
            # Extract token from response
            response_data = response.json()
            self.token = response_data.get("token")
            
            if not self.token:
                raise Exception("No token received from Argo CD")
            
            # Set token in session headers
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            
            logger.info("Successfully logged in to Argo CD")
        except requests.RequestException as e:
            logger.error(f"Exception when logging in to Argo CD: {e}")
            raise
    
    def _extract_ingress_url(self, app_name: str, resources: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract ingress URL from application resources.
        
        Args:
            app_name: Name of the application
            resources: List of application resources
            
        Returns:
            Ingress URL if found, None otherwise
        """
        # First, try to get the application details which might contain external URLs
        try:
            app_url = urljoin(self.host, f"/api/v1/applications/{app_name}")
            response = self.session.get(app_url)
            response.raise_for_status()
            
            app_data = response.json()
            
            # Check if there are external URLs in the status summary
            if "status" in app_data and "summary" in app_data["status"] and "externalURLs" in app_data["status"]["summary"]:
                external_urls = app_data["status"]["summary"]["externalURLs"]
                if external_urls and len(external_urls) > 0:
                    # Return the first external URL
                    return external_urls[0]
        except Exception as e:
            logger.warning(f"Error getting external URLs from application status for {app_name}: {e}")
        
        # If no external URLs found in status, try to extract from ingress resources
        for resource in resources:
            # Check if the resource is an Ingress
            if resource.get("kind") == "Ingress":
                try:
                    name = resource.get("name")
                    namespace = resource.get("namespace")
                    
                    if not name or not namespace:
                        continue
                    
                    # Construct the node path for the resource
                    node_path = f"networking.k8s.io/Ingress/{namespace}/{name}/0"
                    
                    # Use the correct URL format that works
                    resource_url = urljoin(
                        self.host, 
                        f"/api/v1/applications/{app_name}?resource=&node={node_path}"
                    )
                    
                    logger.info(f"Fetching ingress details from: {resource_url}")
                    response = self.session.get(resource_url)
                    response.raise_for_status()
                    
                    # The response structure is different in this API format
                    response_data = response.json()
                    
                    # First check if there are external URLs in the status
                    if "status" in response_data and "summary" in response_data["status"] and "externalURLs" in response_data["status"]["summary"]:
                        external_urls = response_data["status"]["summary"]["externalURLs"]
                        if external_urls and len(external_urls) > 0:
                            # Return the first external URL
                            return external_urls[0]
                    
                    # If no external URLs in status, try to parse the manifest
                    elif "manifest" in response_data:
                        import yaml
                        try:
                            # Parse the manifest YAML
                            ingress_data = yaml.safe_load(response_data["manifest"])
                            
                            # Extract host from ingress rules
                            if "spec" in ingress_data and "rules" in ingress_data["spec"]:
                                for rule in ingress_data["spec"]["rules"]:
                                    if "host" in rule:
                                        # Check if TLS is enabled
                                        protocol = "https" if "tls" in ingress_data["spec"] else "http"
                                        return f"{protocol}://{rule['host']}"
                        except yaml.YAMLError as e:
                            logger.warning(f"Error parsing YAML manifest for ingress {name}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Error extracting ingress URL for resource {name} in app {app_name}: {e}")
                    continue
        
        return None
    
    def get_applications(self) -> List[Dict[str, Any]]:
        """
        Get list of all applications from Argo CD.
        
        Returns:
            List of application dictionaries. Returns an empty list if there's a connection error or timeout.
        """
        if not self.token:
            try:
                self.login()
            except requests.RequestException as e:
                logger.error(f"Failed to login to Argo CD: {e}")
                return []
            
        try:
            apps_url = urljoin(self.host, "/api/v1/applications")
            response = self.session.get(apps_url, timeout=30)  # Adding explicit timeout
            response.raise_for_status()
            
            response_data = response.json()
            applications = response_data.get("items", [])
            
            # Convert to list of dictionaries with selected fields
            app_list = []
            for app in applications:
                metadata = app.get("metadata", {})
                spec = app.get("spec", {})
                status = app.get("status", {})
                sync = status.get("sync", {})
                health = status.get("health", {})
                source = spec.get("source", {})
                destination = spec.get("destination", {})
                resources = status.get("resources", [])
                
                app_name = metadata.get("name")
                
                # First check if there are external URLs in the status summary
                ingress_url = None
                if "summary" in status and "externalURLs" in status["summary"]:
                    external_urls = status["summary"]["externalURLs"]
                    if external_urls and len(external_urls) > 0:
                        ingress_url = external_urls[0]
                
                # If no external URLs found in status summary, try to extract from resources
                if not ingress_url:
                    ingress_url = self._extract_ingress_url(app_name, resources)
                
                app_dict = {
                    "name": app_name,
                    "namespace": metadata.get("namespace"),
                    "project": spec.get("project"),
                    "sync_status": sync.get("status"),
                    "health_status": health.get("status"),
                    "repo": source.get("repoURL"),
                    "path": source.get("path"),
                    "target_revision": source.get("targetRevision"),
                    "destination": {
                        "server": destination.get("server"),
                        "namespace": destination.get("namespace")
                    },
                    "created_at": metadata.get("creationTimestamp"),
                    "ingress_url": ingress_url
                }
                app_list.append(app_dict)
                
            return app_list
        except requests.RequestException as e:
            if isinstance(e, requests.Timeout):
                logger.error(f"Timeout when connecting to Argo CD API: {e}")
            elif isinstance(e, requests.ConnectionError):
                logger.error(f"Connection error when connecting to Argo CD API: {e}")
            else:
                logger.error(f"Exception when calling Argo CD API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error when processing Argo CD API response: {e}")
            return []
    
    def get_application_details(self, name: str) -> Dict[str, Any]:
        """
        Get details of a specific application.
        
        Args:
            name: Name of the application
            
        Returns:
            Application details as dictionary
            
        Raises:
            Exception: If API call fails
        """
        if not self.token:
            self.login()
            
        try:
            app_url = urljoin(self.host, f"/api/v1/applications/{name}")
            response = self.session.get(app_url)
            response.raise_for_status()
            
            app = response.json()
            
            # Extract relevant fields
            metadata = app.get("metadata", {})
            spec = app.get("spec", {})
            status = app.get("status", {})
            sync = status.get("sync", {})
            health = status.get("health", {})
            source = spec.get("source", {})
            destination = spec.get("destination", {})
            resources = status.get("resources", [])
            
            app_name = metadata.get("name")
            
            # First check if there are external URLs in the status summary
            ingress_url = None
            if "summary" in status and "externalURLs" in status["summary"]:
                external_urls = status["summary"]["externalURLs"]
                if external_urls and len(external_urls) > 0:
                    ingress_url = external_urls[0]
            
            # If no external URLs found in status summary, try to extract from resources
            if not ingress_url:
                ingress_url = self._extract_ingress_url(app_name, resources)
            
            # Convert to dictionary
            app_dict = {
                "name": app_name,
                "namespace": metadata.get("namespace"),
                "project": spec.get("project"),
                "sync_status": sync.get("status"),
                "health_status": health.get("status"),
                "repo": source.get("repoURL"),
                "path": source.get("path"),
                "target_revision": source.get("targetRevision"),
                "destination": {
                    "server": destination.get("server"),
                    "namespace": destination.get("namespace")
                },
                "created_at": metadata.get("creationTimestamp"),
                "ingress_url": ingress_url,
                "resources": []
            }
            
            # Add resources if available
            for resource in resources:
                resource_dict = {
                    "kind": resource.get("kind"),
                    "name": resource.get("name"),
                    "namespace": resource.get("namespace"),
                    "status": resource.get("status"),
                    "health_status": resource.get("health", {}).get("status")
                }
                app_dict["resources"].append(resource_dict)
            
            return app_dict
        except requests.RequestException as e:
            logger.error(f"Exception when calling Argo CD API: {e}")
            raise
    
    def get_application_resource(self, app_name: str, resource_name: str, resource_namespace: str, 
                                resource_kind: str, resource_group: Optional[str] = None) -> Dict[str, Any]:
        """
        Get details of a specific resource in an application.
        
        Args:
            app_name: Name of the application
            resource_name: Name of the resource
            resource_namespace: Namespace of the resource
            resource_kind: Kind of the resource (e.g., Ingress, Service)
            resource_group: API group of the resource (e.g., networking.k8s.io)
            
        Returns:
            Resource details as dictionary
            
        Raises:
            Exception: If API call fails
        """
        if not self.token:
            self.login()
            
        try:
            # Construct the node path for the resource
            node_path = f"{resource_group}/{resource_kind}/{resource_namespace}/{resource_name}/0"
            
            # Use the correct URL format that works
            resource_url = urljoin(
                self.host, 
                f"/api/v1/applications/{app_name}?resource=&node={node_path}"
            )
            
            response = self.session.get(resource_url)
            response.raise_for_status()
            
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Exception when calling Argo CD API for resource details: {e}")
            raise
    
    def get_apps_list(self) -> List[AppInfo]:
        """
        Get a simplified list of applications with name, URL, and health status.
        
        Returns:
            List of AppInfo objects containing name, URL, and health status.
            Returns an empty list if there's a connection error or timeout.
        """
        if not self.token:
            try:
                self.login()
            except requests.RequestException as e:
                logger.error(f"Failed to login to Argo CD: {e}")
                return []
            
        try:
            # Get detailed application information first to extract ingress URLs
            detailed_apps = self.get_applications()
            # If get_applications returned an empty list due to an error, just return an empty list
            if not detailed_apps:
                return []
            
            # Convert to list of AppInfo objects
            app_list: List[AppInfo] = []
            for app in detailed_apps:
                name = app.get("name", "")
                # Construct the URL to the application in the Argo CD UI
                argocd_url = urljoin(self.host, f"/applications/{name}")
                health_status = app.get("health_status")
                ingress_url = app.get("ingress_url")
                
                app_info = AppInfo(
                    name=name,
                    url=argocd_url,
                    ingress_url=ingress_url,
                    health_status=health_status
                )
                app_list.append(app_info)
                
            return app_list
        except Exception as e:
            logger.error(f"Exception when processing application list: {e}")
            return []

# Example usage
if __name__ == "__main__":
    # Create Argo CD service
    apphub_service = AppHubService()
    
    # Get applications in simplified format
    try:
        app_list = apphub_service.get_apps_list()
        print(f"Found {len(app_list)} applications:")
        for app in app_list:
            ingress_info = f", Ingress URL: {app.ingress_url}" if app.ingress_url else ""
            print(f"- {app.name} (URL: {app.url}, Health: {app.health_status}{ingress_info})")
    except Exception as e:
        print(f"Error getting applications: {e}") 