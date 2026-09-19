abstract class BaseModuleModel {}

export enum ModuleType {
  PYTHON = 'PYTHON',
}

export enum UploadStatus {
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  INPROGRESS = 'INPROGRESS',
}

export enum AccessMode {
  INTERNAL = 'INTERNAL',
  EXTERNAL = 'EXTERNAL',
}

export enum ModuleExtenstion {
  PY = 'PY',
  ZIP = 'ZIP',
}

export class UploadStats implements BaseModuleModel {
  percentage: string = '';
}

export class ModuleLocation implements BaseModuleModel {
  extension: ModuleExtenstion = ModuleExtenstion.PY;
  path: string = '';
}

export class Module implements BaseModuleModel {
  _id: string | null = null;
  version: string | undefined;
  user_id: string;
  project_id: string;
  site_id: string;
  action_id: string;
  name: string;
  description: string;
  module_type: ModuleType;
  upload_status: UploadStatus;
  upload_stats: UploadStats;
  metadata: { [key: string]: string };
  created_at: Date;
  module_location: ModuleLocation;
  access_mode: AccessMode;
  tags: string[] = [];

  constructor(
    user_id: string,
    project_id: string,
    site_id: string,
    action_id: string,
    name: string,
    description: string,
    module_type: ModuleType,
    upload_status: UploadStatus,
    upload_stats: UploadStats,
    metadata: { [key: string]: string },
    created_at: Date,
    module_location: ModuleLocation,
    access_mode: AccessMode,
    tags: string[],
  ) {
    this.user_id = user_id;
    this.project_id = project_id;
    this.site_id = site_id;
    this.action_id = action_id;
    this.name = name;
    this.description = description;
    this.module_type = module_type;
    this.upload_status = upload_status;
    this.upload_stats = upload_stats;
    this.metadata = metadata;
    this.created_at = created_at;
    this.module_location = module_location;
    this.access_mode = access_mode;
    this.tags = tags;
  }
}

export class ModulesListResponse implements BaseModuleModel {
  modules: Module[] = [];
  total_count: number = 0;

  constructor(modules: Module[], total_count: number) {
    this.modules = modules;
    this.total_count = total_count;
  }
}

export class ModuleUploadResponse implements BaseModuleModel {
  module_id: string = '';
}
