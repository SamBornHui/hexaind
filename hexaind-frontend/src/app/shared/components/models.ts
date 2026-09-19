import { TemplateRef } from '@angular/core';
import { ChartData, ChartOptions, ChartType, PointStyle } from 'chart.js';

export type Direction = 'left' | 'right' | 'top' | 'bottom';
export interface ResizeInfo {
  delta: number;
  direction: Direction;
  width: number;
  height: number;
}
export type InputType =
  | 'color'
  | 'date'
  | 'datetime-local'
  | 'email'
  | 'month'
  | 'number'
  | 'password'
  | 'search'
  | 'tel'
  | 'text'
  | 'time'
  | 'url'
  | 'week'
  | 'select'
  | 'checkbox'
  | 'toggle'
  | 'textarea';

export interface CellInfo {
  column: Column;
  field?: string;
  value: any;
  rowIndex: number;
  columnIndex: number;
  item: SimpleObject;
}
export interface CellChangeInfo extends CellInfo {
  isCellChanged: boolean; // the original value can be restored by editing again.
  isRowChanged: boolean; // the row is changed
}
export type SimpleObject = { [key: string]: any; _rowMeta?: RowMeta };
// ************* API Schema **************
export type AggregateType =
  | 'SUM'
  | 'AVG'
  | 'COUNT'
  | 'COUNT_DISTINCT'
  | 'MAX'
  | 'MIN';

export type ExpressionType = 'SIMPLE' | 'SQL';

export interface Metric {
  expressionType: ExpressionType; // Specifies whether it's a simple aggregator or a custom SQL expression
  label: string; // User-friendly label for the metric (e.g. 'Total Sales', 'Avg Sales per User')
  field?: string; // Column name to be aggregated
  aggregateType?: AggregateType; // Aggregation function (e.g. SUM, AVG, COUNT, COUNT_DISTINCT, MIN, MAX)
  sql?: string; // Arbitrary SQL expression (e.g. 'SUM(sales) / COUNT(distinct user_id)')
  format?: string; // Display formatting string (e.g. '$,.2f', '%.2f', '%,.0f')
}

export type FilterType = '>' | '<' | '=' | '!=' | 'includes' | 'range';

export interface Filter {
  field: string;
  value?: string | number; // compare or search with a value
  to?: string | number; // for range filter
  type?: FilterType; // default is '='
  global?: boolean; // default is true
  targetIds?: string[]; // target ids
}

export type VizType =
  | 'bar'
  | 'line'
  | 'area'
  | 'bubble'
  | 'doughnut'
  | 'pie'
  | 'polarArea'
  | 'scatter'
  | 'table'
  | 'summary'
  | 'boxplot';

export type SortDirection = 'asc' | 'desc' | 'none';
export interface SortInfo {
  field: string;
  direction: SortDirection;
}

export interface Dataset {
  id: string;
  name?: string;
  type?: string; // Application defined type
  url?: string;
  data?: any;
  [key: string]: any;
}

export type DataType = 'string' | 'number' | 'date';

export interface DataColumn {
  name: string;
  type?: DataType; // default is string
}

// While metrics and time_range might be relevant in the future, we can omit them from the current schema as they're not required for the initial implementation.
export interface Query {
  limit?: number;
  metrics?: Metric[];
  filters?: Filter[];
  sorts?: SortInfo[];
  groupby?: string[];
  dataset?: Dataset; // dataset ID or workflow ID or something and meta info for the data source
}

export interface Viz {
  id: string;
  query?: Query;
  name?: string;
  description?: string;
  type?: VizType; // default is bar
  config?: VizConfig; // When being sent to the server, the config should be a string
  data?: any; // data for the viz
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  filters?: Filter[]; // global filters
  config?: DashboardConfig; // When being sent to the server, the config should be a string
  data?: any; // data for the dashboard
}

/**
[
  { id: 'project', name: 'Project Name', defaultValue: 'project-id-0' },
  {
    id: 'step',
    name: 'Step Name',
    parentId: 'project',
    defaultValue: 'step-id-0',
  },
  {
    id: 'tech_node',
    name: 'Tech Node',
    parentId: 'step',
    defaultValue: 'tech-node-id-0',
  },
  {
    id: 'date_range',
    name: 'Date Range',
    parentId: 'tech_node',
    defaultValue: 'date-range-id-0',
  }
]
 */
// /api/dataSources/list
export interface DataSourceFilter {
  id: string; // dataSource filter id
  name: string;
  parentId?: string; // parent dataSource filter id
  defaultValue?: string; // default value for the dataSource items
}

/**
/api/dataSources/list
const projectList: DataSourceData = {
  id: 'project',
  items: [
    { id: 'project-id-0', name: 'Project 1' },
    { id: 'project-id-1', name: 'Project 2' },
  ],
};
/api/dataSources/list?parentIds=project-id-0
const stepList: DataSourceData = {
  id: 'step',
  items: [
    { id: 'step-id-0', name: 'Step 1' },
    { id: 'step-id-1', name: 'Step 2' },
  ],
}
 */
export interface DataSourceData {
  id: string; // dataSource id
  items: IdNameData[]; // dataSource items
}

export interface DatasetDataRequest {
  id: string; // dataset ID, A single ID should be used to link items across multiple filters.
  dataSourceFilterIds?: string[]; // parent dataSource item id list
  filters?: Filter[];
  sorts?: SortInfo[];
}

export interface DatasetData {
  id: string; // dataset ID
  columns: DataColumn[]; // column list
  rows: any[][]; // row data followed the order of the column list
}

const aggregateTypes: AggregateType[] = [
  'SUM',
  'AVG',
  'COUNT',
  'COUNT_DISTINCT',
  'MAX',
  'MIN',
];

export const getAggregateTypeList = () =>
  aggregateTypes.map((type) => ({
    id: type,
    name: type,
  }));
// *************** UI Schema ***************
export const rowLimits = [10, 50, 100, 250, 500, 1000, 5000, 10000];
export const getRowLimitList = () =>
  rowLimits.map((limit) => ({
    id: String(limit),
    name: String(limit),
  }));

export interface VizData {
  isNotReady?: boolean;
  dataset: Dataset;
  columns: DataColumn[];
  rows: { [key: string]: any }[];
}
export type Datas = (VizData | undefined)[][];
export const filterTypes: FilterType[] = [
  'includes',
  'range',
  '>',
  '<',
  '=',
  '!=',
];

export const getFilterTypeList = () =>
  filterTypes.map((type) => ({
    id: type,
    name: type,
  }));

export const vizTypes: VizType[] = [
  'table',
  'bar',
  'line',
  'pie',
  'scatter',
  'boxplot',
];

export type CellStyleType = 'cell' | 'bar';

export const cellStyleTypes: CellStyleType[] = ['cell', 'bar'];

export const getCellStyleTypeList = () =>
  cellStyleTypes.map((type) => ({
    id: type,
    name: type,
  }));

export const getVizTypeList = () => vizTypes.map((t) => ({ id: t, name: t }));

export const getOptionChartTypeList = (baseVizType?: VizType) => {
  const chartTypes = ['bar', 'line', 'boxplot'];
  if (baseVizType === 'scatter') {
    chartTypes.push('scatter');
  }
  return chartTypes.map((type) => ({
    id: type,
    name: type,
  }));
};

export const sortDirections: SortDirection[] = ['asc', 'desc', 'none'];
export const getSortDirectionList = (hideNone = false) => {
  const items = hideNone
    ? sortDirections.filter((item) => item !== 'none')
    : sortDirections;
  return items.map((direction) => ({
    id: direction,
    name: direction,
  }));
};

export interface IdNameData {
  id: string;
  name?: string;
  title?: string;
  [key: string]: any;
}

export interface TreeData extends SimpleObject {
  level: number;
  hasChildren?: boolean;
  expanded?: boolean;
  loading?: boolean;
}

export interface IdNameTreeData extends TreeData, IdNameData {}

export interface IdNameParentNamesData extends IdNameData {
  parentNames: string[];
}

export interface Action {
  name: string;
  data?: any;
}

export interface Size {
  width: number;
  height: number;
}

export interface Column {
  name?: string;
  template?: TemplateRef<any>;
  field?: string;
  className?: string;
  maxWidth?: number;
  minWidth?: number;
  type?: DataType;
  hasSort?: boolean;
  hint?: string;
  defaultSortDirection?: SortDirection;
  editable?: boolean;
  editorInfo?: {
    type?: InputType;
    data?: any; // dropdown items or something. TBD
  };
  styleFn?: (data: any, column: Column, rowIndex: number) => string;
  data?: any;
  _hasCheckbox?: boolean; // internal use
  _hasTreeArrow?: boolean; // internal use
}

// Table row meta data for colSpan etc.
export interface RowMeta {
  colSpans?: {
    index: number;
    count: number;
  }[];
  data?: any;
}

export interface VizDataColumn {
  type?: ChartType;
  field: string;
  options?: VizOptions;
}

export interface LabelDataColumns {
  label: string;
  dataColumns: VizDataColumn[];
}

export interface BubbleColumn {
  x: string;
  y: string;
  r?: string;
}

export interface LabelBubbleColumn {
  label: string;
  bubbleColumn: BubbleColumn;
  options?: VizOptions;
}

export interface CellStyleColumn {
  type?: CellStyleType; // default is text
  filter: Filter;
  options: VizOptions;
}

export interface DashboardCell {
  flex?: number; // flex-grow, default is 1
  viz?: Viz;
}

export interface VizOptions {
  backgroundColor?: string;
  borderColor?: string;
  pointStyle?: PointStyle;
  type?: ChartType;
}

export interface VizConfig {
  labelDataColumns?: LabelDataColumns;
  labelBubbleColumns?: LabelBubbleColumn[];
  cellStyleColumns?: CellStyleColumn[];
  hasDataLabel?: boolean;
}

export interface DashboardCellInfo {
  viz: Viz;
  resizeInfo?: ResizeInfo;
  dataset?: Dataset;
  rowIndex: number;
  cellIndex: number;
}

export const DefaultDashboardRowHeight = 400;
export interface DashboardRow {
  height?: number;
  cells: DashboardCell[];
}
export interface DashboardConfig {
  rows: DashboardRow[];
}

export interface ChartConfig {
  data?: ChartData;
  options?: ChartOptions;
  type?: ChartType;
}

export const getPointStyleList = () => {
  const pointStyles = [
    'circle',
    'cross',
    'crossRot',
    'dash',
    'line',
    'rect',
    'rectRounded',
    'rectRot',
    'star',
    'triangle',
  ];
  return pointStyles.map((style) => ({
    id: style,
    name: style,
  }));
};

export interface PageInfo {
  index: number;
  offset: number;
  limit: number;
}
