from datetime import datetime, timezone

from app.services.access_controls.roles.schemas import ProjectBasedFeatures, DatasetBasedFeatures, MLModelBasedFeatures, \
    ConnectorBasedFeatures, WorkflowsBasedFeatures, RecipeBasedFeatures, AssetsBasedFeatures, JupyterToolBasedFeatures, \
    DSGToolBasedFeatures, ToolBasedFeatures, JobBasedFeatures, HelpSupportBasedFeatures, ResourcesBasedFeatures, \
    ManageUsersInProjectBasedFeatures, SystemGeneratedProjectRoles, RolesFeaturesMap, RoleType, RoleCreationType, ProjectAdminBasedFeatures


def generate_features_for_project_administrator():
    dataset_based_features = DatasetBasedFeatures(
        create=True, read=True, update=True, delete=True)
    ml_model_features = MLModelBasedFeatures(
        create=True, read=True, update=True, delete=True)
    connector_based_features = ConnectorBasedFeatures(
        create=True, read=True, update=True, delete=True)
    workflows_based_features = WorkflowsBasedFeatures(
        create=True, read=True, update=True, delete=True, execute=True, publish=True, update_versioned=True)
    recipes_based_features = RecipeBasedFeatures(
        create=True, read=True, update=True, delete=True, execute=True)
    jupyter_based_features = JupyterToolBasedFeatures(execute=True)
    dsg_tool_based_features = DSGToolBasedFeatures(execute=True)
    jobs_based_features = JobBasedFeatures(read=True)
    help_based_features = HelpSupportBasedFeatures(read=True)

    assets_based_features = AssetsBasedFeatures(datasets=dataset_based_features,
                                                ml_models=ml_model_features,
                                                workflows=workflows_based_features,
                                                recipes=recipes_based_features,
                                                connectors=connector_based_features)
    tool_based_features = ToolBasedFeatures(
        jupyter=jupyter_based_features, dsg_tool=dsg_tool_based_features)
    resource_based_features = ResourcesBasedFeatures(
        jobs=jobs_based_features, help_support=help_based_features)
    manage_users_based_features = ManageUsersInProjectBasedFeatures(
        add=True, read=True, modify=True, delete=True)
    project_based_feature = ProjectAdminBasedFeatures(
        create=True, read=True, update=True, delete=True)

    features = ProjectBasedFeatures(assets=assets_based_features, tools=tool_based_features,
                                    resources=resource_based_features, manage_project_users=manage_users_based_features, projects=project_based_feature)
    return features


def generate_features_for_full_access():
    dataset_based_features = DatasetBasedFeatures(
        create=True, read=True, update=True, delete=True)
    ml_model_features = MLModelBasedFeatures(
        create=True, read=True, update=True, delete=True)
    connector_based_features = ConnectorBasedFeatures(
        create=True, read=True, update=True, delete=True)
    workflows_based_features = WorkflowsBasedFeatures(
        create=True, read=True, update=True, delete=True, execute=True, publish=True, update_versioned=True)
    recipes_based_features = RecipeBasedFeatures(
        create=True, read=True, update=True, delete=True, execute=True)
    jupyter_based_features = JupyterToolBasedFeatures(execute=True)
    dsg_tool_based_features = DSGToolBasedFeatures(execute=True)
    jobs_based_features = JobBasedFeatures(read=True)
    help_based_features = HelpSupportBasedFeatures(read=True)

    assets_based_features = AssetsBasedFeatures(datasets=dataset_based_features,
                                                ml_models=ml_model_features,
                                                workflows=workflows_based_features,
                                                recipes=recipes_based_features,
                                                connectors=connector_based_features)
    tool_based_features = ToolBasedFeatures(
        jupyter=jupyter_based_features, dsg_tool=dsg_tool_based_features)
    resource_based_features = ResourcesBasedFeatures(
        jobs=jobs_based_features, help_support=help_based_features)
    manage_users_based_features = ManageUsersInProjectBasedFeatures()

    features = ProjectBasedFeatures(assets=assets_based_features, tools=tool_based_features,
                                    resources=resource_based_features, manage_project_users=manage_users_based_features)
    return features


def generate_features_for_limited_access():
    dataset_based_features = DatasetBasedFeatures(
        create=False, read=True, update=False, delete=False)
    ml_model_features = MLModelBasedFeatures(
        create=False, read=True, update=False, delete=False)
    connector_based_features = ConnectorBasedFeatures(
        create=False, read=False, update=False, delete=False)
    workflows_based_features = WorkflowsBasedFeatures(
        create=False, read=True, update=False, delete=False, execute=True, publish=False, update_versioned=True)
    recipes_based_features = RecipeBasedFeatures(
        create=False, read=False, update=False, delete=False, execute=False)
    jupyter_based_features = JupyterToolBasedFeatures(execute=False)
    dsg_tool_based_features = DSGToolBasedFeatures(execute=False)
    jobs_based_features = JobBasedFeatures(read=True)
    help_based_features = HelpSupportBasedFeatures(read=False)

    assets_based_features = AssetsBasedFeatures(datasets=dataset_based_features,
                                                ml_models=ml_model_features,
                                                workflows=workflows_based_features,
                                                recipes=recipes_based_features,
                                                connectors=connector_based_features)
    tool_based_features = ToolBasedFeatures(
        jupter=jupyter_based_features, dsg_tool=dsg_tool_based_features)
    resource_based_features = ResourcesBasedFeatures(
        jobs=jobs_based_features, help_support=help_based_features)
    manage_users_based_features = ManageUsersInProjectBasedFeatures()

    features = ProjectBasedFeatures(assets=assets_based_features, tools=tool_based_features,
                                    resources=resource_based_features, manage_project_users=manage_users_based_features)
    return features


def get_system_generated_role_features_map(role):
    if role == SystemGeneratedProjectRoles.PROJECT_ADMINISTRATOR:
        features = generate_features_for_project_administrator()
        _id = "6602fe187e593b9e70a60b3e"
    elif role == SystemGeneratedProjectRoles.FULL_ACCESS:
        features = generate_features_for_full_access()
        _id = "6602fe18ed1470d7309c6f8e"
    elif role == SystemGeneratedProjectRoles.LIMITED_ACCESS:
        features = generate_features_for_limited_access()
        _id = "6602fe18ed1470d7309c6f8d"
    else:
        raise Exception(f"unknown role for system generated roles: {role}")
    role_name = str(role.value)
    return RolesFeaturesMap(
        _id=_id,
        name=role_name,
        description=f"Auto generated role by server",
        role_type=RoleType.PROJECT_ROLE,
        features=features,
        created_at='2024-03-27T06:23:46.948952',
        is_active=True,
        last_modified_at='2024-03-27T06:23:46.948952',
        source_type=RoleCreationType.SYSTEM_GENERATED_ROLE
    )
