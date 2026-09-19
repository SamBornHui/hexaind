import { WidgetClientType } from '../pages/workflow-designer/client-tags';
import { Notification } from './notification-models';
import { Project } from './project-models';
import { User } from './user-models';
import { WidgetType, Workflow, WorkflowRun } from './workflow-models';

export interface UpdateWorkflowResponse {
  success: boolean;
}

export interface GetFilesPostResponse {
  files: any;
  file_names: [];
  file_path: [];
}

export interface GetFilesNames {
  file_names: [];
  file_path: [];
}

export interface UserGetResponse {
  users: User[];
}

export interface ServerResponse {
  name: string;
  description: string;
  project_id: string;
  status: string;
  last_activity: string;
  launch_url: string;
  notebooks: any[];
}

export interface TransformedServerResponse {
  server_id: string;
  server_name: string;
  server_description: string;
  project_id: string;
  project_name: string;
  server_status: string;
  launch_url: string;
  last_activity: string;
  actions: {
    can_delete: boolean;
    can_start: boolean;
    can_stop: boolean;
  };
}

export interface ProjectGetResponse {
  projects: Project[];
  total_count: number;
}

export interface GetCustomPythonWidgetRecipeResponse {
  succeeded: boolean;
  results: CustomPythonWidgetRecipe[];
  count: number;
  message: string;
}

export interface WidgetInputRules {
  count: number;
  cofig: any[];
}

export interface CustomPythonWidgetSettings {
  color_ode: string;
  allow_users_to_modify_configurations: boolean;
}

export interface CustomPythonWidgetRecipe {
  version: string;
  _id: string;
  name: string;
  recipe_name: string;
  description: string;
  reference_links: string[];
  tags: string[] | null;
  widget_inputs_rules: WidgetInputRules | null;
  widget_outputs_rules: WidgetInputRules | null;
  module_id: string;
  inputs_map: InputMap[];
  outputs_map: OutputMap[];
  settings: CustomPythonWidgetSettings;
  help_details: any;
  project_id: string;
  site_id: string;
  access_mode: string;
  created_by: string;
  created_at: Date;
  last_modified_by: string;
  last_modified_at: Date;
}

export interface GetCustomCodeResponse {
  succeeded: boolean;
  results: CustomPythonWidgetRecipe[];
  message: string;
}

export interface CustomCode {
  type: WidgetType;
  clientType: WidgetClientType;
  iconName: string;
  displayName: string;
  id: string | null;
  description?: string | null;
  // Remove the 'name' property if it's not relevant for all widgets
}

export interface InputMap {
  arg_name: string;
  type: string;
  default_value: string;
  is_mandatory: boolean;
  is_widget_input: boolean;
  mapped_input: any; // Depending on your data structure, this could be of a specific type
}

export interface OutputMap {
  key_name: string;
  reference_name: string;
  type: string;
}

export interface ProjectPostResponse {
  project_id: string;
}

export interface CreatePasswordResponse {
  email: string;
  reason: string;
}

export interface RunWorkflowPostResponse {
  run_id: string;
}

export interface GetWorkflowsResponse {
  workflows: Workflow[];
  workflows_count: number;
  page_number: number;
  page_limit: number;
}

export class ActivityLog {
  time: string | undefined = undefined;
  log_level: string | undefined = undefined;
  message: string | undefined = undefined;
  exc_info: string | undefined = undefined;
}

export interface ActivityLogResponse {
  logs: ActivityLog[];
  new_cursor_timestamp: string;
  new_cursor_id: string;
}

export interface GetWorkflowResponse {
  workflow: Workflow;
}

export interface NotificationsGetResponse {
  notification: Notification[];
}

export interface GetWorkflowsRunsResponse {
  runs: WorkflowRun[];
  total_count: number;
}

export interface GetProjectResponse {
  project: Project;
}

export interface PostCSVResponse {
  dataset_id: string;
}

export interface InputCount {
  count: number | undefined;
}

export interface SchemaGetResponse {
  inputs: InputCount;
}

export class FileNodeResponse {
  name: string | undefined = undefined;
  full_path: string | undefined = undefined;
  type: string | undefined = undefined;
  children: FileNodeResponse[] = [];
  trail: number | undefined;
  widget: string | undefined = undefined;
  loaded: boolean = false;
}

export class FileStructureNodeResponse {
  name: string | undefined = undefined;
  full_path: string | undefined = undefined;
  type: string | undefined = undefined;
  children: FileStructureNodeResponse[] = [];
  size: string | undefined = undefined;
  last_modified_at: string | undefined = undefined;
  created_by: string | undefined = undefined;
  _id: string | undefined = undefined;
}
