from datetime import datetime, timezone

from app.services.admin.projects.schemas import CreateNewProjectRequest, Project


def convert_create_new_project_request_to_project(site_id: str, user_id: str,
                                                  create_project_request: CreateNewProjectRequest):
    return Project(
        name=create_project_request.name,
        description=create_project_request.description,
        site_id=site_id,
        owner_id=create_project_request.project_administrator_id,
        owner_name=create_project_request.project_administrator_name,
        created_by=user_id,
        created_at=datetime.now(timezone.utc),
        last_modified_by_id=user_id,
        last_modified_at=datetime.now(timezone.utc),
        shared_with=[user_role_mapping.user_id for user_role_mapping in create_project_request.users_roles_mappings]
    )