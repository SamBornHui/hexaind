import { WidgetType } from './workflow-models';

abstract class BaseDataModel {}

export enum DatasetType {
  TABULAR = 'TABULAR',
  IMAGE = 'IMAGE',
  PDF = 'PDF',
}

export enum UploadStatus {
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  INPROGRESS = 'INPROGRESS',
}

export enum GraphType {
  DISTRIBUTION = 'DISTRIBUTION',
  CONTOUR = 'CONTOUR',
  SPLINEFIT = 'SPLINEFIT',
  LINEARFIT = 'LINEARFIT',
}

export enum AccessMode {
  INTERNAL = 'INTERNAL',
  EXTERNAL = 'EXTERNAL',
}
export enum TabularColumnType {
  NUMERICAL = 'NUMERICAL',
  CATEGORICAL = 'CATEGORICAL',
}

export class UploadStats implements BaseDataModel {
  percentage: string = '';
}

export class DatasetLocation implements BaseDataModel {
  isfolder: boolean;
  size: string;
  extension: string;
  path: string;
  last_modified_by: string | undefined;
  last_modified_at: string | undefined;

  constructor(
    isfolder: boolean,
    size: string,
    extension: string,
    path: string,
  ) {
    this.isfolder = isfolder;
    this.size = size;
    this.extension = extension;
    this.path = path;
  }
}

export class ColumnStatistics implements BaseDataModel {
  name: string;
  type: TabularColumnType;
  parameters: { [key: string]: string };

  constructor(
    name: string,
    type: TabularColumnType,
    parameters: { [key: string]: string },
  ) {
    this.name = name;
    this.type = type;
    this.parameters = parameters;
  }
}

export class Visualization implements BaseDataModel {
  x_axis: string;
  y_axis: string;
  graph: string;
  graph_type: GraphType;
  color_by: string;

  constructor(
    x_axis: string,
    y_axis: string,
    graph: string,
    graph_type: GraphType,
    color_by: string,
  ) {
    this.x_axis = x_axis;
    this.y_axis = y_axis;
    this.graph = graph;
    this.graph_type = graph_type;
    this.color_by = color_by;
  }
}

export class DatasetSchema implements BaseDataModel {
  column_name: string;
  data_type: string;

  constructor(column_name: string, data_type: string) {
    this.column_name = column_name;
    this.data_type = data_type;
  }
}

export class TabularDatasetInformation implements BaseDataModel {
  preview: { [key: string]: string } | undefined;
  statistics: ColumnStatistics[] | undefined = [];
  visualize: Visualization[] | undefined = [];
  schema: DatasetSchema[] | undefined = [];
}

export class RescaleMediaFiles implements BaseDataModel {
  trail_number: string | undefined = undefined;
  media_files: DatasetLocation[] = [];
}

class RescaleWidgetCustomInformation implements BaseDataModel {
  trail_data: RescaleMediaFiles[] = [];
}

export class WorkflowDatasetCustomInformation {
  widget_type: WidgetType | undefined = undefined;
  custom_information: RescaleWidgetCustomInformation | undefined = undefined;
}

export class Dataset implements BaseDataModel {
  _id: string | null = null;
  version: string | undefined;
  user_id: string;
  project_id: string;
  site_id: string;
  action_id: string;
  name: string;
  description: string;
  dataset_type: DatasetType;
  dataset_information: TabularDatasetInformation[] = [];
  upload_status: UploadStatus;
  upload_stats: UploadStats;
  metadata: { [key: string]: string };
  created_at: Date;
  dataset_location: DatasetLocation[] = [];
  access_mode: AccessMode;
  tags: string[] = [];
  custom_information: WorkflowDatasetCustomInformation[] = [];

  constructor(
    user_id: string,
    project_id: string,
    site_id: string,
    action_id: string,
    name: string,
    description: string,
    dataset_type: DatasetType,
    upload_status: UploadStatus,
    upload_stats: UploadStats,
    metadata: { [key: string]: string },
    created_at: Date,
    dataset_location: DatasetLocation[],
    access_mode: AccessMode,
    tags: string[],
  ) {
    this.user_id = user_id;
    this.project_id = project_id;
    this.site_id = site_id;
    this.action_id = action_id;
    this.name = name;
    this.description = description;
    this.dataset_type = dataset_type;
    this.upload_status = upload_status;
    this.upload_stats = upload_stats;
    this.metadata = metadata;
    this.created_at = created_at;
    this.dataset_location = dataset_location;
    this.access_mode = access_mode;
    this.tags = tags;
  }
}

export class AssetsListResponse {
  datasets: Dataset[] = [];
  total_count: number = 0;

  constructor(datasets: Dataset[], total_count: number) {
    this.datasets = datasets;
    this.total_count = total_count;
  }
}
