import { getRGBAByIndex } from 'src/app/shared/components/charts/chart-utils';
import { Dashboard } from 'src/app/shared/components/models';

const dashboardList: Dashboard[] = [
  {
    id: '0',
    name: 'My dashboard 01',
    description: 'My description',
    config: {
      rows: [
        {
          cells: [
            {
              flex: 2,
              viz: {
                id: '2d9e795d-b25b-48a1-94ae-90a5cda5e1bc',
                name: 'Alabama',
                config: {
                  labelDataColumns: {
                    label: 'city',
                    dataColumns: [
                      {
                        field: 'latitude',
                        options: {
                          backgroundColor: getRGBAByIndex(0, 0.2),
                          borderColor: getRGBAByIndex(0),
                        },
                      },
                      {
                        field: 'longitude',
                        options: {
                          backgroundColor: getRGBAByIndex(1, 0.2),
                          borderColor: getRGBAByIndex(1),
                        },
                      },
                    ],
                  },
                  labelBubbleColumns: [
                    {
                      bubbleColumn: {
                        x: 'latitude',
                        y: 'longitude',
                      },
                      label: 'x:latitude|y:longitude',
                      options: {
                        backgroundColor: getRGBAByIndex(0, 0.2),
                        borderColor: getRGBAByIndex(0),
                      },
                    },
                  ],
                },
                query: {
                  dataset: {
                    id: 'Alabama',
                    name: 'Alabama',
                    country: 'US',
                  },
                  filters: [],
                  sorts: [],
                },
                type: 'scatter',
              },
            },
            {
              viz: {
                id: '313a08ca-d5d3-4f5d-bf3c-219f5a2130de',
                name: 'Arizona',
                config: {
                  labelDataColumns: {
                    label: 'city',
                    dataColumns: [{ field: 'population' }],
                  },
                },
                query: {
                  dataset: {
                    id: 'Arizona',
                    name: 'Arizona',
                    country: 'US',
                  },
                  filters: [],
                },
                type: 'line',
              },
            },
          ],
        },
        {
          cells: [
            {
              viz: {
                id: '7d087d1d-c420-4465-935f-f9a7d6ed7d7d',
                name: 'California',
                config: {},
                query: {
                  dataset: {
                    id: 'California',
                    name: 'California',
                    country: 'US',
                  },
                },
                type: 'table',
              },
            },
          ],
        },
      ],
    },
  },
  {
    id: '1',
    name: 'My dashboard 02',
    description: 'My description',
    config: {
      rows: [
        {
          cells: [
            {
              viz: {
                id: '7ec7f51e-74ea-4812-9dda-3c610790d01b',
                name: 'Alabama',
                config: {},
                query: {
                  dataset: {
                    id: 'Alabama',
                    name: 'Alabama',
                    country: 'US',
                  },
                },
                type: 'table',
              },
            },
            {
              viz: {
                id: '662759cc-663f-4fe1-b3fe-e21d4ae9f593',
                name: 'Alabama',
                config: {
                  labelDataColumns: {
                    label: 'city',
                    dataColumns: [{ field: 'population' }],
                  },
                },
                query: {
                  dataset: {
                    id: 'Alabama',
                    name: 'Alabama',
                    country: 'US',
                  },
                  filters: [],
                },
                type: 'bar',
              },
            },
            {
              viz: {
                id: '6d494b63-e689-46e0-a689-97f1e00a2300',
                name: 'Alabama',
                config: {
                  labelDataColumns: {
                    label: 'city',
                    dataColumns: [
                      { field: 'latitude', type: 'bar' },
                      { field: 'longitude' },
                    ],
                  },
                },
                query: {
                  dataset: {
                    id: 'Alabama',
                    name: 'Alabama',
                    country: 'US',
                  },
                  filters: [],
                },
                type: 'line',
              },
            },
          ],
        },
        {
          cells: [
            {
              viz: {
                id: 'e72472f7-5401-4f06-bb27-1d8978aa7a13',
                name: 'Alabama',
                config: {
                  labelDataColumns: {
                    label: 'city',
                    dataColumns: [{ field: 'population' }],
                  },
                },
                query: {
                  dataset: {
                    id: 'Alabama',
                    name: 'Alabama',
                    country: 'US',
                  },
                  filters: [],
                },
                type: 'pie',
              },
            },
            {
              flex: 2,
              viz: {
                id: '9c98ffc3-b2d2-44e8-a086-ff37d5d439f2',
                name: 'Alabama',
                config: {},
                query: {
                  dataset: {
                    id: 'Alabama',
                    name: 'Alabama',
                    country: 'US',
                  },
                },
                type: 'table',
              },
            },
          ],
        },
      ],
    },
  },
];

export const getDashboardList = () => dashboardList;

export const getDataSourceFilters = () => [
  { id: 'project', name: 'Project Name', api: 'api/projects' },
  {
    id: 'step',
    name: 'Step Name',
    parentIds: ['project'],
    api: 'api/projects/[project_id]/steps',
  },
  {
    id: 'tech_node',
    name: 'Tech Node',
    parentIds: ['project', 'step'],
    api: 'api/projects/[project_id]/steps/[step_id]/techNodes',
  },
  {
    id: 'date_range',
    name: 'Date Range',
    parentIds: ['project', 'step', 'tech_node'],
    api: 'api/projects/[project_id]/steps/[step_id]/techNodes/[tech_node_id]/dateRanges',
  },
  {
    id: 'output_column_name',
    name: 'Output Column Name',
    parentIds: ['project', 'step', 'tech_node', 'date_range'],
    api: 'api/projects/[project_id]/steps/[step_id]/techNodes/[tech_node_id]/dateRanges/[date_range_id]/output_column_names',
  },
];

export const getDataSourceFilter = () => [
  {
    id: 'data_sources',
    name: 'Data Sources',
    api: 'api/projects/[project_id]/steps/[step_id]/techNodes/[tech_node_id]/dateRanges/[date_range_id]/output_column_names',
  },
];
