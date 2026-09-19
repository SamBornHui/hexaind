from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.services.admin.authentication.schemas import User


class SupersetRole(BaseModel):
    id: int
    name: str


class SupersetRoleService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def from_id(self, id: int) -> SupersetRole:
        response = await self._client.get(f"/api/v1/security/roles/{id}")
        if not response.is_success:
            raise KeyError(f"Role {id} not found")
        return SupersetRole.model_validate(response.json()["result"])

    async def get_all(self) -> List[SupersetRole]:
        payload = {
            "page_size": -1,
        }
        response = await self._client.get(
            "/api/v1/security/roles/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [SupersetRole.model_validate(role) for role in response.json()["result"]]

    async def from_name(self, name: str, exact: bool = True) -> List[SupersetRole]:
        payload = {
            "filters": [
                {
                    "col": "name",
                    "opr": "eq" if exact else "ct",
                    "value": name,
                }
            ]
        }
        response = await self._client.get(
            "/api/v1/security/roles/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [SupersetRole.model_validate(role) for role in response.json()["result"]]

    async def create(self, name: str) -> SupersetRole:
        payload = {"name": name}
        response = await self._client.post("/api/v1/security/roles/", json=payload)
        if not response.is_success:
            raise ValueError(response.json()["message"])
        result = response.json()
        return SupersetRole.model_validate(
            {"id": result["id"], "name": result["result"]["name"]}
        )

    async def delete(self, id: int):
        response = await self._client.delete(f"/api/v1/security/roles/{id}")
        if not response.is_success:
            raise ValueError(response.json()["message"])

    async def get_permissions(self, id: int) -> List[SupersetPermissionResource]:
        response = await self._client.get(f"/api/v1/security/roles/{id}/permissions/")
        if not response.is_success:
            raise ValueError(response.json()["message"])
        return [
            SupersetPermissionResource.model_validate(
                {
                    "id": item["id"],
                    "permission_name": item["permission_name"],
                    "resource_name": item["view_menu_name"],
                }
            )
            for item in response.json()["result"]
        ]

    async def update_permissions(
        self, id: int, permission_resources: List[SupersetPermissionResource]
    ):
        payload = {
            "permission_view_menu_ids": list(
                {permission_resource.id for permission_resource in permission_resources}
            )
        }
        response = await self._client.post(
            f"/api/v1/security/roles/{id}/permissions", json=payload
        )
        print(response.json())
        if not response.is_success:
            raise ValueError(response.json()["message"])


class SupersetUser(BaseModel):
    id: int
    active: bool
    email: str
    first_name: str
    last_name: str
    username: str
    roles: List[SupersetRole]


class SupersetUserService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def from_id(self, id: int) -> SupersetUser:
        response = await self._client.get(f"/api/v1/security/users/{id}")
        if not response.is_success:
            raise KeyError(f"User {id} not found")
        return SupersetUser.model_validate(response.json()["result"])

    async def get_all(self) -> List[SupersetUser]:
        payload = {
            "page_size": -1,
        }
        response = await self._client.get(
            "/api/v1/security/users/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [SupersetUser.model_validate(user) for user in response.json()["result"]]

    async def from_email(self, email: str) -> List[SupersetUser]:
        payload = {
            "filters": [
                {
                    "col": "email",
                    "opr": "eq",
                    "value": email,
                }
            ]
        }
        response = await self._client.get(
            "/api/v1/security/users/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [SupersetUser.model_validate(role) for role in response.json()["result"]]

    async def create(
        self,
        email: str,
        first_name: str,
        last_name: str,
        username: str,
        password: str,
        active: bool = True,
        roles: Optional[List[SupersetRole]] = None,
    ) -> SupersetUser:
        payload = {
            "active": active,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "password": password,
            "roles": [role.id for role in roles] if roles is not None else [4, 5],
        }
        response = await self._client.post("/api/v1/security/users/", json=payload)
        if not response.is_success:
            raise ValueError(response.json()["message"])
        return await self.from_id(response.json()["id"])

    async def update(self, user: User):
        if user.data_superset is None:
            raise ValueError("superset data not found")
        payload = {
            "active": True,
            "email": str(user.email),
            "first_name": user.first_name if user.first_name else "",
            "last_name": user.last_name if user.last_name else "",
            "username": str(user.email),
            "password": user.data_superset.password,
            "roles": user.data_superset.role,
        }
        response = await self._client.put(
            f"/api/v1/security/users/{user.data_superset.superset_user_id}",
            json=payload,
        )
        if not response.is_success:
            raise ValueError(response.json()["message"])

    async def delete(self, id: int):
        response = await self._client.delete(f"/api/v1/security/users/{id}")
        if not response.is_success:
            raise ValueError(response.json()["message"])


class SupersetPermission(BaseModel):
    id: int
    name: str


class SupersetPermissionService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def from_id(self, id: int) -> SupersetPermission:
        response = await self._client.get(f"/api/v1/security/permissions/{id}")
        if not response.is_success:
            raise KeyError(f"Permission {id} not found")
        return SupersetPermission.model_validate(response.json()["result"])

    async def get_all(self) -> List[SupersetPermission]:
        payload = {
            "page_size": -1,
        }
        response = await self._client.get(
            "/api/v1/security/permissions/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [
            SupersetPermission.model_validate(permission)
            for permission in response.json()["result"]
        ]

    async def from_name(
        self, name: str, exact: bool = True
    ) -> List[SupersetPermission]:
        payload = {
            "filters": [
                {
                    "col": "name",
                    "opr": "eq" if exact else "ct",
                    "value": name,
                }
            ]
        }
        response = await self._client.get(
            "/api/v1/security/permissions/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [
            SupersetPermission.model_validate(permission)
            for permission in response.json()["result"]
        ]


class SupersetResource(BaseModel):
    id: int
    name: str


class SupersetResourceService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def from_id(self, id: int) -> SupersetResource:
        response = await self._client.get(f"/api/v1/security/resources/{id}")
        if not response.is_success:
            raise KeyError(f"Resource {id} not found")
        return SupersetResource.model_validate(response.json()["result"])

    async def get_all(self) -> List[SupersetResource]:
        payload = {
            "page_size": -1,
        }
        response = await self._client.get(
            "/api/v1/security/resources/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [
            SupersetResource.model_validate(permission)
            for permission in response.json()["result"]
        ]

    async def from_name(self, name: str) -> List[SupersetResource]:
        payload = {
            "filters": [
                {
                    "col": "name",
                    "opr": "ct",
                    "value": name,
                }
            ]
        }
        response = await self._client.get(
            "/api/v1/security/resources/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [
            SupersetResource.model_validate(permission)
            for permission in response.json()["result"]
        ]

    async def from_database_id(self, id: int) -> List[SupersetResource]:
        payload = {
            "filters": [
                {
                    "col": "name",
                    "opr": "ew",
                    "value": f"(id:{id})",
                }
            ]
        }
        response = await self._client.get(
            "/api/v1/security/resources/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [
            SupersetResource.model_validate(permission)
            for permission in response.json()["result"]
        ]


class SupersetPermissionResource(BaseModel):
    id: int = Field(frozen=True)
    permission_name: str
    resource_name: str

    model_config = ConfigDict(frozen=True)


class SupersetPermissionResourceService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def from_id(self, id: int) -> SupersetPermissionResource:
        response = await self._client.get(
            f"/api/v1/security/permissions-resources/{id}"
        )
        if not response.is_success:
            raise KeyError(f"Permission Resource {id} not found")
        result = response.json()["result"]
        permission_name = result["permission"]["name"]
        resource_name = result["view_menu"]["name"]
        return SupersetPermissionResource.model_validate(
            {
                "id": id,
                "permission_name": permission_name,
                "resource_name": resource_name,
            }
        )

    async def from_permission_resource(
        self, permission_id: int, resource_id: int
    ) -> List[SupersetPermissionResource]:
        payload = {
            "filters": [
                {"col": "permission", "opr": "rel_o_m", "value": permission_id},
                {"col": "view_menu", "opr": "rel_o_m", "value": resource_id},
            ]
        }
        response = await self._client.get(
            "/api/v1/security/permissions-resources/", params={"q": json.dumps(payload)}
        )
        if not response.is_success:
            return []
        return [
            SupersetPermissionResource.model_validate(
                {
                    "id": permission_resource["id"],
                    "permission_name": permission_resource["permission"]["name"],
                    "resource_name": permission_resource["view_menu"]["name"],
                }
            )
            for permission_resource in response.json()["result"]
        ]


class SupersetDatabase(BaseModel):
    id: int
    name: str


class SupersetDatabaseService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def from_id(self, id: int) -> SupersetDatabase:
        response = await self._client.get(f"/api/v1/database/{id}")
        if not response.is_success:
            raise KeyError(f"Database {id} not found")
        return SupersetDatabase.model_validate(
            {"id": id, "name": response.json()["result"]["database_name"]}
        )

    async def create(self, payload: Dict[str, Any]) -> SupersetDatabase:
        response = await self._client.post("/api/v1/database/", json=payload)
        if not response.is_success:
            raise ValueError(response.json()["message"])
        id = response.json()["id"]
        return await self.from_id(id)


class SupersetService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self.role = SupersetRoleService(client)
        self.user = SupersetUserService(client)
        self.permision = SupersetPermissionService(client)
        self.resource = SupersetResourceService(client)
        self.permission_resource = SupersetPermissionResourceService(client)
        self.database = SupersetDatabaseService(client)

    @staticmethod
    async def authenticate_and_create_client(
        url: str,  # = "http://172.31.144.44:8088",
        username: str,  # = "admin",
        password: str,  # = "admin",
    ):
        """Authenticate and create an instance of SupersetService."""
        client = httpx.AsyncClient(base_url=url, timeout=None)
        response = await client.post(
            "/api/v1/security/login",
            json={
                "password": password,
                "provider": "db",
                "refresh": True,
                "username": username,
            },
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        client.headers["Authorization"] = f"Bearer {token}"
        return SupersetService(client)

    async def __aenter__(self) -> SupersetService:
        """Enter the asynchronous context (similar to __enter__)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the asynchronous context (similar to __exit__)."""
        await self.logout()
        await self._client.aclose()

    async def logout(self):
        """Log out the current user and close the session."""
        response = await self._client.post("/api/v1/security/logout")
        response.raise_for_status()
        await self._client.aclose()
        return response.json()

    async def close(self):
        """Close the HTTP client session."""
        await self._client.aclose()
