import { WorkflowClientTags } from '../pages/workflow-designer/client-tags';
import { Widget, Workflow } from './workflow-models';

export enum ActionResultType {
  DATASET = 'DATASET',
  STRING = 'STRING',
  MODEL = 'MODEL',
  FAILURE = 'FAILURE',
  JSON = 'JSON',
  VISUALIZATION = 'VISUALIZATION',
  STRINGS_LIST = 'STRINGS_LIST',
}

export interface SavedWorkflow {
  workflow_id: string;
  workflow_version: string;
  name: string;
  description: string;
}

export class SessionSaveAsWorkflow {
  name: string | undefined = undefined;
  version_tag: string | undefined = undefined;
  description: string | undefined = undefined;
  user_id: string | undefined = undefined;
  user_name: string | undefined = undefined;
}

export class SessionWorkflow {
  widgets: Widget[] = [];
  start: string[] = [];
  end: string[] = [];
  user_id: string | undefined = undefined;
  user_name: string | undefined = undefined;
  client_tags: WorkflowClientTags | undefined = undefined;
}

export class WidgetStatus {
  urn: string | undefined = undefined;
  status: string | undefined = undefined;
}

export class WorkflowRunStatus {
  workflow: Workflow | undefined = undefined;
  widgets_status: WidgetStatus[] = [];
  run_status: string | undefined = undefined;
  is_single_widget_run: any;
}

export class VersionedWorkflowRunStatus {
  workflow: Workflow | undefined = undefined;
  widgets_status: WidgetStatus[] = [];
}

export class SaveAsSessionWorkflowPostResponseClass {
  workflow_id: string | undefined = undefined;
}

export class WorkflowSession {
  version: string | undefined = undefined;
  _id: string | null = null;
  name: string | undefined = undefined;
  description: string | undefined = undefined;
  workflow_id: string | undefined = undefined;
  saved_workflows: SavedWorkflow[] = [];
  run_id: string | undefined = undefined;
  owner_id: string | undefined = undefined;
  owner_name: string | undefined = undefined;
  created_at: Date | undefined = undefined;
  last_modified_by_id: string | undefined = undefined;
  last_modified_at: Date | undefined = undefined;
  project_id: string | undefined = undefined;
  site_id: string | undefined = undefined;
  is_template: boolean | undefined = undefined;
}

export class WorkflowSessionCreateUpdateBody {
  version: string;
  name: string;
  description: string;
  owner_id: string;
  owner_name: string;

  constructor(
    version: string,
    name: string,
    description: string,
    ownerName: string,
    ownerId: string,
  ) {
    this.version = version;
    this.name = name;
    this.description = description;
    this.owner_id = ownerId;
    this.owner_name = ownerName;
  }
}

export class SessionCreateResponse {
  version: string | undefined = undefined;
  session_id: string | undefined = undefined;
}

export class WorkflowSessions {
  sessions: WorkflowSession[] = [];
  sessions_count: number = 0;
  page_number: number = 0;
  page_limit: number = 0;
}

export class UploadStats {
  percentage: string | undefined = undefined;
}

export class DatasetLocation {
  isfolder: boolean = true;
  size: string | undefined = undefined;
  extension: string | undefined = undefined;
  path: string | undefined = undefined;
  last_modified_by: string | undefined = undefined;
  last_modified_at: Date | undefined = undefined;
}

export interface CustomInformation {
  widget_type: string;
  custom_information: {
    trail_data: TrailData[];
  };
}

// Interface for trail data
export interface TrailData {
  trail_number: string;
  media_files: MediaFile[];
}

// Interface for media files within trail data
export interface MediaFile {
  isfolder: boolean;
  size: number; // Representing file size in bytes
  extension: string;
  path: string;
  last_modified_by: string | null;
  last_modified_at: string; // As a date string or Date object
}


export class DatasetWidgetResult {
  _id: string | undefined = undefined;
  version: string | undefined = undefined;
  user_id: string | undefined = undefined;
  project_id: string | undefined = undefined;
  site_id: string | undefined = undefined;
  action_id: string | undefined = undefined;
  description: string | undefined = undefined;
  dataset_type: string | undefined = undefined;
  dataset_information: any[] = [];
  upload_status: string | undefined = undefined;
  upload_stats: UploadStats | undefined = undefined;
  created_at: Date | undefined = undefined;
  dataset_location: DatasetLocation [] = [];
  access_mode: string | undefined = undefined;
  tags: string[] = [];
  output_name: string | undefined = undefined;
  custom_information: CustomInformation | undefined;
  name: string | undefined = undefined;
  file_path_value: string | undefined = undefined;
}

export class FailureActionResult {
  error_code: string | undefined = undefined;
  error_description: string | undefined = undefined;
}

export class StringActionResult {
  string_value: string | undefined = undefined;
}

export class StringListActionResult {
  strings_list_value: string[] = [];
}

export class JSONActionResult {
  json_value: string | undefined = undefined;
}

export class WidgetRunResult {
  result_type: ActionResultType | undefined = undefined;
  result_value:
    | DatasetWidgetResult
    | FailureActionResult
    | StringActionResult
    | JSONActionResult
    | StringListActionResult
    | undefined = undefined;

  output_name: string[] = [];
}
