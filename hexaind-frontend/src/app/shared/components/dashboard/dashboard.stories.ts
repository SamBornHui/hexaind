import { Component } from '@angular/core';
import { type Meta, type StoryObj } from '@storybook/angular';
import { generateColumnsAndRows } from 'src/tests/mocks/mocks';
import { Dashboard, DashboardCellInfo, Datas, VizData } from '../models';
import { DashboardComponent } from './dashboard.component';

@Component({
  selector: 'mst-dashboard-example',
  template: `
    <mst-dashboard
      [config]="config"
      [datas]="datas"
      (vizDataLoad)="onVizDataLoad($event)"
    />
  `,
  standalone: true,
  imports: [DashboardComponent],
})
export class DashboardExampleComponent {
  config = getDashboardConfig();
  datas: Datas = [];
  onVizDataLoad({ viz, rowIndex, cellIndex }: DashboardCellInfo) {
    if (viz.query?.dataset?.id) {
      const data = getData(viz.query.dataset.id);
      this.datas[rowIndex] = this.datas[rowIndex] || [];
      this.datas[rowIndex][cellIndex] = data;
    }
  }
}

const meta: Meta<DashboardExampleComponent> = {
  title: 'Components/Dashboard',
  component: DashboardExampleComponent,
};

export default meta;
type Story = StoryObj<DashboardExampleComponent>;

export const Primary: Story = {};

//*********** mocked data **********/
function getDashboardConfig() {
  const config: Dashboard = {
    id: '67c7548ab922b4cf98497608',
    name: 'My dashboard',
    description: 'My dashboard description',
    config: {
      rows: [
        {
          cells: [
            {
              viz: {
                id: '67c8cc35b922b4cf98497ebc',
                name: 'test1',
                description: '',
                type: 'bar',
                query: {
                  limit: 10,
                  metrics: [],
                  filters: [],
                  sorts: [],
                  dataset: {
                    id: '67c0ed0a2700bb76a16867cb',
                    name: 'test1',
                    type: 'dataset',
                  },
                  groupby: [],
                },
                config: {
                  labelDataColumns: {
                    label: 'State',
                    dataColumns: [
                      {
                        field: 'iPhone Sales (in million units)',
                        options: {
                          backgroundColor: 'rgba(54, 162, 235,0.2)',
                          borderColor: 'rgba(54, 162, 235,1)',
                          pointStyle: 'circle',
                        },
                      },
                      {
                        field: 'iPad Sales (in million units)',
                        options: {
                          backgroundColor: 'rgba(255, 99, 132,0.2)',
                          borderColor: 'rgba(255, 99, 132,1)',
                          pointStyle: 'circle',
                        },
                      },
                    ],
                  },
                  labelBubbleColumns: [],
                  cellStyleColumns: [],
                },
              },
              flex: 1.5318627450980393,
            },
            {
              viz: {
                id: '67c8cc37b922b4cf98497ed2',
                name: '1100x600',
                description: '',
                type: 'table',
                query: {
                  limit: 1000,
                  metrics: [],
                  filters: [],
                  sorts: [],
                  dataset: {
                    id: '67c2025cb922b4cf984963a6',
                    name: '1100x600',
                    type: 'dataset',
                  },
                  groupby: [],
                },
                config: {
                  labelDataColumns: {
                    label: '',
                    dataColumns: [],
                  },
                  labelBubbleColumns: [],
                  cellStyleColumns: [
                    {
                      filter: {
                        field: 'Column0',
                        value: '2-1',
                        global: true,
                        type: 'includes',
                      },
                      options: {
                        borderColor: 'rgba(54, 162, 235,1)',
                        backgroundColor: 'rgba(54, 162, 235,0.2)',
                      },
                    },
                    {
                      filter: {
                        field: 'Column1',
                        value: '3-',
                        global: true,
                        type: 'includes',
                      },
                      options: {
                        borderColor: 'rgba(255, 99, 132,1)',
                        backgroundColor: 'rgba(255, 99, 132,0.2)',
                      },
                    },
                  ],
                },
              },
              flex: 1,
            },
          ],
          height: 520,
        },
        {
          cells: [
            {
              viz: {
                id: '67c9ee73b922b4cf984993a9',
                name: 'test1',
                description: '',
                type: 'line',
                query: {
                  limit: 50,
                  metrics: [],
                  filters: [],
                  sorts: [],
                  dataset: {
                    id: '67c0ed0a2700bb76a16867cb',
                    name: 'test1',
                    type: 'dataset',
                  },
                  groupby: [],
                },
                config: {
                  labelDataColumns: {
                    label: 'State',
                    dataColumns: [
                      {
                        field: 'iPhone Sales (in million units)',
                        options: {
                          backgroundColor: 'rgba(54, 162, 235,0.2)',
                          borderColor: 'rgba(54, 162, 235,1)',
                          pointStyle: 'circle',
                        },
                      },
                      {
                        field: 'iPad Sales (in million units)',
                        options: {
                          backgroundColor: 'rgba(255, 99, 132,0.2)',
                          borderColor: 'rgba(255, 99, 132,1)',
                          pointStyle: 'circle',
                        },
                      },
                      {
                        field: 'Mac Sales (in million units)',
                        options: {
                          backgroundColor: 'rgba(75, 192, 192,0.2)',
                          borderColor: 'rgba(75, 192, 192,1)',
                          pointStyle: 'circle',
                        },
                      },
                    ],
                  },
                  labelBubbleColumns: [],
                  cellStyleColumns: [
                    {
                      filter: {
                        field: 'State',
                        value: '',
                      },
                      options: {
                        borderColor: 'rgba(54, 162, 235,1)',
                        backgroundColor: 'rgba(54, 162, 235,0.2)',
                      },
                    },
                  ],
                },
              },
            },
          ],
          height: 358,
        },
      ],
    },
    filters: [
      {
        field: 'State',
        type: 'includes',
        value: 'ch',
        to: '',
        global: false,
        targetIds: ['67c8cc35b922b4cf98497ebc', '67c8cc37b922b4cf98497ed2'],
      },
    ],
  };
  return config;
}

function getData(id: string) {
  const { columns, items: rows } = generateColumnsAndRows(100, 100, 0, false);
  const data: any = {
    '67c0ed0a2700bb76a16867cb': {
      dataset: {
        id: '67c0ed0a2700bb76a16867cb',
        name: 'test1',
        type: 'dataset',
      },
      columns: [
        {
          name: 'State',
          type: 'string',
        },
        {
          name: 'Region',
          type: 'string',
        },
        {
          name: 'iPhone Sales (in million units)',
          type: 'number',
        },
        {
          name: 'iPad Sales (in million units)',
          type: 'number',
        },
        {
          name: 'Mac Sales (in million units)',
          type: 'number',
        },
        {
          name: 'Wearables (in million units)',
          type: 'number',
        },
        {
          name: 'Services Revenue (in billion $)',
          type: 'number',
        },
      ],
      rows: [
        {
          State: 'Chongqing',
          Region: 'Greater China',
          'iPhone Sales (in million units)': 7.46,
          'iPad Sales (in million units)': 6.75,
          'Mac Sales (in million units)': 1.19,
          'Wearables (in million units)': 5.88,
          'Services Revenue (in billion $)': 15.88,
        },
        {
          State: 'Germany',
          Region: 'Europe',
          'iPhone Sales (in million units)': 8.63,
          'iPad Sales (in million units)': 14.06,
          'Mac Sales (in million units)': 7.03,
          'Wearables (in million units)': 7.42,
          'Services Revenue (in billion $)': 10.12,
        },
        {
          State: 'UK',
          Region: 'Europe',
          'iPhone Sales (in million units)': 5.61,
          'iPad Sales (in million units)': 14.09,
          'Mac Sales (in million units)': 8.78,
          'Wearables (in million units)': 8.19,
          'Services Revenue (in billion $)': 19.85,
        },
        {
          State: 'Shanghai',
          Region: 'Greater China',
          'iPhone Sales (in million units)': 7.82,
          'iPad Sales (in million units)': 7.97,
          'Mac Sales (in million units)': 9.78,
          'Wearables (in million units)': 2.28,
          'Services Revenue (in billion $)': 6.16,
        },
        {
          State: 'Thailand',
          Region: 'Rest of Asia',
          'iPhone Sales (in million units)': 16.7,
          'iPad Sales (in million units)': 8.13,
          'Mac Sales (in million units)': 6.46,
          'Wearables (in million units)': 3.48,
          'Services Revenue (in billion $)': 13.29,
        },
        {
          State: 'Chongqing',
          Region: 'Greater China',
          'iPhone Sales (in million units)': 12.18,
          'iPad Sales (in million units)': 10.97,
          'Mac Sales (in million units)': 9.38,
          'Wearables (in million units)': 11.65,
          'Services Revenue (in billion $)': 12.7,
        },
        {
          State: 'UK',
          Region: 'Europe',
          'iPhone Sales (in million units)': 25.47,
          'iPad Sales (in million units)': 7.41,
          'Mac Sales (in million units)': 7.18,
          'Wearables (in million units)': 7.56,
          'Services Revenue (in billion $)': 17.2,
        },
        {
          State: 'New York',
          Region: 'North America',
          'iPhone Sales (in million units)': 22.37,
          'iPad Sales (in million units)': 6.74,
          'Mac Sales (in million units)': 4.39,
          'Wearables (in million units)': 3.22,
          'Services Revenue (in billion $)': 16.07,
        },
        {
          State: 'Mexico',
          Region: 'Rest of World',
          'iPhone Sales (in million units)': 20.8,
          'iPad Sales (in million units)': 6.79,
          'Mac Sales (in million units)': 4.99,
          'Wearables (in million units)': 2.68,
          'Services Revenue (in billion $)': 8.69,
        },
        {
          State: 'Italy',
          Region: 'Europe',
          'iPhone Sales (in million units)': 9.06,
          'iPad Sales (in million units)': 9.14,
          'Mac Sales (in million units)': 8.99,
          'Wearables (in million units)': 2.66,
          'Services Revenue (in billion $)': 6.01,
        },
      ],
    },
    '67c2025cb922b4cf984963a6': {
      dataset: {
        id: '67c2025cb922b4cf984963a6',
        name: '1100x600',
        type: 'dataset',
      },
      columns,
      rows,
    },
  };
  console.log(data);
  return data[id] as VizData;
}
