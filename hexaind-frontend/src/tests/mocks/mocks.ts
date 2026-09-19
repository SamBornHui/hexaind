import {
  Column,
  Dashboard,
  DataColumn,
  DatasetData,
  SortInfo,
  Viz,
} from 'src/app/shared/components/models';
import { sortData } from 'src/app/shared/utils/utils';
import { delay, getRandomNumber } from '../test-utils';
import { countriesAndStates } from './cities';

export const loadData = async (
  {
    offset,
    limit,
  }: {
    offset: number;
    limit: number;
  },
  rowCount = 1000,
  columnCount = 10,
  sortInfo?: SortInfo,
) => {
  await delay(getRandomNumber(500, 3000));
  const { columns, items } = generateColumnsAndRows(limit, columnCount, offset);
  return {
    columns,
    items: sortInfo ? sortData(items, [sortInfo]) : items,
    isLastPage: offset + limit >= rowCount,
  };
};

export const generateColumnsAndRows = (
  rowCount = 999,
  colCount = 10,
  offset = 0,
  hasIdName = true,
) => {
  const columns: Column[] = Array(colCount)
    .fill(null)
    .map((_val, index) => ({
      name: `Column${index}`,
      field: hasIdName
        ? index === 0
          ? 'id'
          : index === 1
            ? 'name'
            : `Column${index}`
        : `Column${index}`,
    }));
  const items = Array(rowCount)
    .fill(null)
    .map((_rowVal, rowIndex) => {
      const row: any = {};
      columns.map((_colVal, colIndex) => {
        return (row[columns[colIndex].field || ''] = `Data ${
          rowIndex + 1 + offset
        }-${colIndex + 1}`);
      });
      row['parentNames'] = ['Workflow' + rowIndex, 'Widget', 'Output'];
      return row;
    });
  return { columns, items };
};

export const generateCsvData = (
  rowCount = 999,
  colCount = 10,
  delimiter = ',',
) => {
  const { columns, items } = generateColumnsAndRows(rowCount, colCount);
  const header = columns.map((col) => col.name).join(delimiter);
  const rows = items.map((row) =>
    columns.map((col) => row[col.field || '']).join(delimiter),
  );
  return [header, ...rows].join('\n');
};

export const generateList = (rowCount = 999, prefix = '') => {
  return Array(rowCount)
    .fill(null)
    .map((_, i) => ({
      id: `${prefix}list-id-${i}`,
      name: `${prefix}list-name-${i}`,
    }));
};

export const generateArrayItems = (arr: any[]) =>
  arr.map((name) => ({ id: name, name }));

const eyeColors = ['brown', 'blue', 'hazel', 'gray', 'green', 'red', 'violet'];
const sex = ['male', 'female'];

export const generateUserInfo = (count = 99) => {
  return Array(count)
    .fill(null)
    .map((_, i) => {
      const countryInfo = countriesAndStates[i % countriesAndStates.length];
      const country = countryInfo.abbreviation;
      const state = countryInfo.states[i % countryInfo.states.length].name;
      return {
        name: `user-name ${i}`,
        email: `email${i}@testemail.com`,
        age: getRandomNumber(0, 110),
        sex: sex[getRandomNumber(0, 1)],
        country,
        state,
        income: getRandomNumber(10000, 1000000),
        height: getRandomNumber(150, 200),
        weight: getRandomNumber(40, 150),
        eyeColor: eyeColors[getRandomNumber(0, eyeColors.length - 1)],
        description: `Description ${i}: Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.`,
      };
    });
};

export const viz01: Viz = {
  id: 'viz01',
  name: 'viz name 01',
  description: 'description 01',
  config: { labelDataColumns: { label: '', dataColumns: [] } },
  query: {
    sorts: [{ field: 'name', direction: 'asc' }],
  },
  type: 'line',
};

const viz02: Viz = {
  id: 'viz02',
  name: 'viz name 02',
  type: 'pie',
};

const viz03: Viz = {
  id: 'viz03',
  name: 'widget name 03',
  type: 'pie',
};

// pivot?
// Dashboard will have only rows for now.
// If we want to have column layout, `widgets` will be `widgetsOrItems` to support the column layout.
const dashboardConfig: Dashboard = {
  id: 'dashboard01',
  name: 'Dashboard 01',
  description: 'Dashboard 01 description',
  config: {
    rows: [
      {
        height: 200,
        cells: [
          {
            flex: 2,
            viz: { ...viz01 },
          },
          {
            viz: { ...viz02 },
          },
          {
            viz: { ...viz03 },
          },
        ],
      },
      {
        height: 200,
        cells: [{}, {}],
      },
      {
        height: 200,
        cells: [{}, {}, {}],
      },
    ],
  },
};

const city = {
  city: 'New York',
  growth_from_2000_to_2013: '4.8%',
  latitude: 40.7127837,
  longitude: -74.0059413,
  population: '8405837',
  rank: '1',
  state: 'New York',
};

export const convertObejctKeysToColumnNames = (o: { [key: string]: any }) =>
  Object.keys(o).map((key) => ({ name: key }));

export const convertJsonToVizData = (
  columns: DataColumn[],
  row: { [key: string]: any },
) =>
  columns.reduce((item: string[], { name }) => {
    item.push(row[name]);
    return item;
  }, []);

export const convertJsonToVizDatas = (
  rows: { [key: string]: any }[],
): DatasetData => {
  const columns = convertObejctKeysToColumnNames(rows[0]);
  const items = rows.map((row) => convertJsonToVizData(columns, row));
  return {
    id: 'test-dataset',
    columns,
    rows: items,
  };
};

/**
 * Filter apis will load a dropdown to select a child filter or something.
 * `api/projects` will return the project list, so that a user can select a project.
 * example: {items: [{id: 'project01', name: 'Project 01'}, ...]}
 * When selecting `project01`, it will load the step names with api `api/projects/project01/steps`
 * example: {items: [{id: 'step01', name: 'Step 01'}, ...]}
 * When selecting `step01`, it will load the tech nodes with api `api/projects/project01/steps/step01/techNodes`
 * example: {items: [{id: 'techNode01', name: 'Tech Node 01'}, ...]}
 * ...
 */
export const dataSetList = {
  filters: [
    { id: 'project', name: 'Project Name', api: 'api/projects' },
    {
      id: 'step',
      name: 'Step Name',
      parentFilterIds: ['project'],
      api: 'api/projects/[project_id]/steps',
    },
    {
      id: 'tech_node',
      name: 'Tech Node',
      parentFilterIds: ['project', 'step'],
      api: 'api/projects/[project_id]/steps/[step_id]/techNodes',
    },
    {
      id: 'date_range',
      name: 'Date Range',
      parentFilterIds: ['project', 'step', 'tech_node'],
      api: 'api/projects/[project_id]/steps/[step_id]/techNodes/[tech_node_id]/dateRanges',
    },
    {
      id: 'output_column_name',
      name: 'Output Column Name',
      parentFilterIds: ['project', 'step', 'tech_node', 'date_range'],
      api: 'api/projects/[project_id]/steps/[step_id]/techNodes/[tech_node_id]/dateRanges/[date_range_id]/output_column_names',
    },
  ],
  items: [
    { id: 1, name: 'Data Set1', api: 'api/xxx/xxx' }, // data set api will load data to display the visualization.
    { id: 2, name: 'Data Set2', api: 'api/xxx/yyy' },
  ],
};

export const TimestampMock = '2024-03-04T23:48:18.952078+00:00';
export const LongDescription =
  '\nLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore ' +
  'magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo ' +
  'consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. ' +
  'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. ' +
  '\n\n\n\n#### Dies Illa' +
  '\n- quantus tremor est futurus' +
  '\n- quando judex est venturus' +
  '\n- cuncta stricte discussurus';
export const getMockString = (name: string, type: string, i = 0, suffix = '') =>
  `${name}${type ? `-${type}` : ''}-${i + 1}${suffix ? `-${suffix}` : ''}`;
export const getMockId = (name: string, i = 0) => getMockString(name, 'id', i);
export const getMockName = (name: string, i = 0) =>
  getMockString(name, 'name', i);
export const getMockDesc = (
  name: string,
  i = 0,
  longDesc = false,
  hasNull = true,
) =>
  hasNull && i % 3 === 0
    ? ''
    : `${getMockString(name, 'description', i)} ${
        longDesc ? LongDescription : ''
      }`;

export const getIdNameItems = (prefix: string, count = 20) =>
  Array(count)
    .fill(null)
    .map((_null, i) => ({
      id: getMockId(prefix, i),
      name: getMockName(prefix, i),
      description: getMockDesc(prefix, i),
    }));

export const getPrefixAndIdFromId = (id: string): string[] => id.split('-id-');

interface Item {
  id: number; // ID is now a number
  name: string;
  nodeType: 'workflow' | 'run' | 'widget' | 'output';
  draggable?: boolean;
  rightIconNames?: string[];
  children: Item[];
}

let nextItemId = 1; // Initialize a counter for generating IDs

export function generateNestedArray(numWorkflows: number): Item[] {
  const items: Item[] = [];

  for (let i = 0; i < numWorkflows; i++) {
    const workflow: Item = {
      id: nextItemId++, // Assign the current ID and increment it
      name: `Workflow ${i + 1}`,
      nodeType: 'workflow',
      children: [],
    };

    const numRuns = Math.floor(Math.random() * 5) + 1;

    for (let j = 0; j < numRuns; j++) {
      const run: Item = {
        id: nextItemId++,
        name: `Run ${j + 1}`,
        nodeType: 'run',
        children: [],
      };

      const numWidgets = Math.floor(Math.random() * 4) + 1;
      for (let k = 0; k < numWidgets; k++) {
        const widget: Item = {
          id: nextItemId++,
          name: `Widget ${k + 1}`,
          nodeType: 'widget',
          children: [],
        };

        const numOutputs = Math.floor(Math.random() * 3) + 1;
        for (let l = 0; l < numOutputs; l++) {
          const output: Item = {
            id: nextItemId++,
            name: `Output ${l + 1}`,
            nodeType: 'output',
            draggable: true,
            rightIconNames: ['drag_indicator'],
            children: [],
          };
          widget.children.push(output);
        }
        run.children.push(widget);
      }
      workflow.children.push(run);
    }
    items.push(workflow);
  }

  return items;
}
