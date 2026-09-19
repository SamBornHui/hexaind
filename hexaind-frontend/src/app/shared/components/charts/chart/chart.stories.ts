import type { Meta, StoryObj } from '@storybook/angular';
import { bubbles, months, numbers } from 'src/tests/test-utils';
import { getColors, getRGBAByIndex } from '../chart-utils';
import { ChartComponent } from './chart.component';

const meta: Meta<ChartComponent> = {
  title: 'Components/Chart',
  component: ChartComponent,
  args: {},
};

export default meta;
type Story = StoryObj<ChartComponent>;

export const Bar: Story = {
  args: {
    config: {
      data: {
        labels: [
          'January',
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
        ],
        datasets: [
          {
            label: 'Sales',
            data: [12, 19, 3, 5, 2, 3, 7],
            backgroundColor: getRGBAByIndex(0, 0.2),
            borderColor: getRGBAByIndex(0),
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
        plugins: {
          datalabels: {
            display: false,
          },
        },
      },
    },
  },
};

export const BarBorderRadius: Story = {
  args: {
    config: {
      data: {
        labels: months({ count: 7 }),
        datasets: [
          {
            label: 'Fully Rounded',
            data: numbers({ count: 7, min: -100, max: 100 }),
            backgroundColor: getRGBAByIndex(0, 0.5),
            borderColor: getRGBAByIndex(0),
            borderWidth: 2,
            borderRadius: Number.MAX_VALUE,
            borderSkipped: false,
          },
          {
            label: 'Small Radius',
            data: numbers({ count: 7, min: -100, max: 100 }),
            backgroundColor: getRGBAByIndex(1, 0.5),
            borderColor: getRGBAByIndex(1),
            borderWidth: 2,
            borderRadius: 5,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Bar Chart',
          },
          datalabels: {
            display: false,
          },
        },
      },
    },
  },
};

export const Line: Story = {
  args: {
    config: {
      data: {
        labels: months({ count: 7 }),
        datasets: [
          {
            label: 'Dataset 1',
            data: numbers({ count: 7, min: -100, max: 100 }),
            backgroundColor: getRGBAByIndex(0, 0.5),
            borderColor: getRGBAByIndex(0),
          },
          {
            label: 'Dataset 2',
            data: numbers({ count: 7, min: -100, max: 100 }),
            backgroundColor: getRGBAByIndex(1, 0.5),
            borderColor: getRGBAByIndex(1),
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Line Chart',
          },
          datalabels: {
            display: false,
          },
        },
      },
      type: 'line',
    },
  },
};

export const Pie: Story = {
  args: {
    config: {
      data: {
        labels: ['Red', 'Orange', 'Yellow', 'Green', 'Blue'],
        datasets: [
          {
            label: 'Dataset 1',
            data: numbers({ count: 5, min: 0, max: 100 }),
            backgroundColor: getColors(),
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Pie Chart',
          },
          datalabels: {
            formatter: (value, context) => {
              let sum = 0;
              const dataArr = context.chart.data.datasets[0].data;
              dataArr.forEach((data) => {
                sum += data as number;
              });

              const percentage = ((+value * 100) / sum).toFixed(2) + '%';
              return percentage;
            },
            color: '#fff',
            font: {
              weight: 'bold',
              size: 20,
            },
          },
        },
      },
      type: 'pie',
    },
  },
};

export const Scatter: Story = {
  args: {
    config: {
      data: {
        datasets: [
          {
            label: 'Dataset 1',
            data: bubbles({ count: 7, rmin: 1, rmax: 1, min: 0, max: 100 }),
            borderColor: getRGBAByIndex(0),
            backgroundColor: getRGBAByIndex(0, 0.5),
          },
          {
            label: 'Dataset 2',
            data: bubbles({ count: 7, rmin: 1, rmax: 1, min: 0, max: 100 }),
            borderColor: getRGBAByIndex(1),
            backgroundColor: getRGBAByIndex(1, 0.5),
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Scatter Chart',
          },
          datalabels: {
            display: false,
          },
        },
      },
      type: 'scatter',
    },
  },
};

export const ScatterWithLine: Story = {
  args: {
    config: {
      data: {
        datasets: [
          {
            label: 'Dataset 1',
            data: bubbles({ count: 10, rmin: 1, rmax: 1, min: 0, max: 100 }),
            borderColor: getRGBAByIndex(0),
            backgroundColor: getRGBAByIndex(0, 0.5),
          },
          {
            label: 'Dataset 2',
            data: bubbles({ count: 10, rmin: 1, rmax: 1, min: 0, max: 100 }),
            borderColor: getRGBAByIndex(1),
            backgroundColor: getRGBAByIndex(1, 0.5),
          },
          {
            label: 'Line Dataset 1',
            data: bubbles({ count: 2, rmin: 1, rmax: 1, min: 0, max: 100 }),
            borderColor: getRGBAByIndex(2),
            backgroundColor: getRGBAByIndex(2, 0.5),
            type: 'line',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Scatter with Line Chart',
          },
          datalabels: {
            display: false,
          },
        },
      },
      type: 'scatter',
    },
  },
};

export const Boxplot: Story = {
  args: {
    config: {
      data: {
        labels: [
          'Chongqing',
          'Germany',
          'UK',
          'Shanghai',
          'Thailand',
          'New York',
          'Mexico',
          'Italy',
          'Hong Kong',
          'Canada',
          'Japan',
          'Spain',
          'Australia',
          'Beijing',
          'India',
          'Texas',
          'California',
          'South Africa',
          'Brazil',
          'Florida',
          'Illinois',
          'South Korea',
          'Indonesia',
          'Shenzhen',
          'France',
        ],
        datasets: [
          {
            label: 'iPhone Sales (in million units)',
            data: [
              [
                7.46, 12.18, 7.92, 11.79, 19.66, 17.47, 27.24, 21.82, 22.7,
                9.58, 18.26, 15.18, 28.38,
              ],
              [8.63, 10.31, 28.52, 21.12, 25.89, 22.89],
              [
                5.61, 25.47, 23.34, 19.55, 24.97, 18.18, 18.79, 20.84, 26.58,
                19.23, 22.52,
              ],
              [7.82, 14.08, 27.23, 9.25, 12.93, 8.32, 22.97, 16.45, 13.7],
              [16.7, 28.65],
              [22.37, 25.2, 23.19, 21.51, 8.66],
              [20.8, 15.92, 15.4, 5.16, 24.1, 17.71, 17.8, 25.99, 25.83],
              [9.06, 23.49, 28.53, 12.41, 6.58, 6.25],
              [
                5.58, 23.29, 13.42, 10.97, 12.99, 20.42, 28.27, 26.67, 14.89,
                22.22, 27.23, 24.97, 28.94, 16.45, 17.95,
              ],
              [12.28, 29.01, 21.58, 20.51, 27.98, 20.49, 17.84, 24.23, 27.99],
              [16.12, 16.91, 17.39, 6.1, 23.13, 16.41, 10.91],
              [14.08, 16.08, 29.36, 25.98],
              [
                8.1, 10.45, 16.36, 5.63, 13.33, 16.34, 10.12, 15.88, 20.42,
                9.11, 6.49, 15.75,
              ],
              [
                11.85, 28.38, 22.58, 7.38, 16.75, 29.66, 13.45, 18.88, 24.19,
                21.44,
              ],
              [23.69, 13.12, 8.5, 9.31, 12.54, 10.51],
              [24.11, 11.16, 27.91, 22.05, 26.36, 14.44, 7.01],
              [
                11.12, 23.96, 21.14, 14.87, 28.25, 8.87, 24.08, 6.76, 13.34,
                15.49, 23.31,
              ],
              [
                27.37, 16.2, 11.78, 11.88, 25.8, 16.84, 20.18, 7.78, 9.63,
                24.19, 5.2, 24.94, 14.24, 19.55,
              ],
              [29.86, 25.24, 11.79, 7.39, 12.57, 26.48, 26.13, 13.58],
              [12.6, 5.75, 11.33, 19.95],
              [21.37, 29.67, 15.51, 27.31, 27.66, 25.43],
              [15.76, 6.85, 15.57, 28.24, 24.84, 16.55, 6.89],
              [6.38, 16.98, 22.14, 15.37, 7.41, 11.55],
              [28.7, 8.41, 13.86, 25.08, 28.8, 29.84, 25.6, 16.23],
              [7.66, 6.28, 9.22, 28.25, 5.37],
            ],
            backgroundColor: 'rgba(54, 162, 235,0.2)',
            borderColor: 'rgba(54, 162, 235,1)',
            borderWidth: 1,
            itemStyle: 'circle',
            itemBackgroundColor: 'rgba(54, 162, 235,1)',
            outlierBackgroundColor: 'rgba(54, 162, 235,1)',
            itemRadius: 3,
          },
          {
            label: 'iPad Sales (in million units)',
            data: [
              [
                6.75, 10.97, 8.77, 7.05, 11.05, 8.26, 14.61, 9.37, 7.95, 13.9,
                6.79, 12.82, 6.12,
              ],
              [14.06, 10.27, 14.61, 11.98, 11.99, 14.29],
              [14.09, 7.41, 9.22, 10.51, 5.38, 2.08, 6.59, 2.74, 7.73, 7.92, 9],
              [7.97, 4.66, 11.11, 2.44, 10.29, 2.34, 3.83, 4.59, 10.82],
              [8.13, 13.65],
              [6.74, 14.4, 5.47, 12.58, 6.15],
              [6.79, 8.53, 11.95, 6.95, 14.35, 3.88, 7.49, 8.02, 11.65],
              [9.14, 8.08, 7.37, 10.8, 10.3, 6.44],
              [
                5.78, 13.29, 3.79, 4.94, 7.3, 8.76, 8.25, 11.15, 7.7, 5.35,
                9.22, 11.3, 4.17, 10.27, 9.49,
              ],
              [6.65, 12.32, 9.81, 7.61, 4.88, 13.08, 12.84, 7.93, 2.18],
              [14.89, 6.2, 10.56, 8.47, 12.58, 2.51, 8.68],
              [9.92, 3.88, 8.34, 3.33],
              [
                13.87, 3.08, 14.36, 5.92, 5.5, 5.63, 4.78, 13.2, 14.97, 2.11,
                5.45, 6.93,
              ],
              [3.43, 4.85, 12.33, 7.05, 14.07, 10.99, 6.05, 8.92, 8.27, 6.84],
              [2.77, 2.58, 3.96, 9.3, 7.68, 4.76],
              [4.93, 12.83, 8.84, 9.66, 10.12, 13.33, 13.03],
              [
                14.08, 10.33, 2.96, 14.94, 9.16, 3.59, 9.3, 8.9, 8.37, 9.53,
                10.77,
              ],
              [
                3.27, 9.09, 14.17, 8.57, 4.4, 13.52, 6.75, 12.56, 8.45, 9.13,
                5.26, 11.63, 12.67, 6.88,
              ],
              [9.45, 3.68, 9.07, 4.25, 14.67, 11.96, 4.03, 11.45],
              [9.68, 9.95, 4.33, 11.25],
              [9.84, 6.05, 3.73, 8.27, 12.94, 3.15],
              [12.14, 10.25, 12.04, 13.67, 11.35, 10.73, 11.78],
              [2.24, 5.83, 9.47, 8.22, 2.77, 4.38],
              [12.21, 5.95, 3.85, 4.84, 4.74, 5.28, 4.44, 9.37],
              [4.35, 9.86, 7.62, 3.97, 8],
            ],
            backgroundColor: 'rgba(255, 99, 132,0.2)',
            borderColor: 'rgba(255, 99, 132,1)',
            borderWidth: 1,
            itemStyle: 'circle',
            itemBackgroundColor: 'rgba(255, 99, 132,1)',
            outlierBackgroundColor: 'rgba(255, 99, 132,1)',
            itemRadius: 3,
          },
          {
            label: 'Mac Sales (in million units)',
            data: [
              [
                1.19, 9.38, 5.19, 8.33, 4.6, 4.76, 5.57, 2.48, 9.98, 5.88, 4.76,
                6.19, 6.39,
              ],
              [7.03, 8.84, 1.66, 2.3, 6.55, 3.96],
              [8.78, 7.18, 6.47, 6.56, 4.7, 3.47, 6.56, 1.83, 5.96, 2.37, 5.55],
              [9.78, 8.77, 2.33, 9.97, 1.57, 6.9, 5.52, 7.94, 3.33],
              [6.46, 3.67],
              [4.39, 8, 4.97, 9.46, 3.11],
              [4.99, 5.42, 9.7, 9, 1.15, 5.41, 8.35, 7.33, 1.26],
              [8.99, 2.34, 9.16, 8.7, 4.63, 5.5],
              [
                5.89, 2.59, 4.91, 2.82, 4.49, 8.74, 5.57, 6.43, 8.16, 1.65,
                7.54, 5.57, 5.74, 3.21, 6.06,
              ],
              [4.37, 7.66, 9.31, 3.31, 5.99, 8.06, 8.57, 2.89, 2.39],
              [7.61, 3.21, 9.93, 4.43, 6.1, 9.37, 6.63],
              [2.07, 4.36, 5.44, 9.17],
              [
                7.77, 7.61, 2.98, 2.45, 6.3, 9.88, 8.32, 4.9, 5.11, 5.68, 4.03,
                4.86,
              ],
              [4.48, 7, 6.81, 3.47, 3.48, 3.72, 8.29, 6.09, 4.97, 3.63],
              [3.9, 3.63, 9.52, 1.5, 8.8, 4.46],
              [1.48, 2.06, 9.78, 5.08, 8.15, 8.36, 5.94],
              [4.5, 8.94, 3.26, 8.61, 1.22, 5.94, 4.65, 2.62, 3.44, 5.19, 7.3],
              [
                5.54, 6.42, 7.16, 9.03, 6.84, 1.88, 3.52, 6.9, 6.68, 6.07, 1.51,
                4.15, 5.55, 2.3,
              ],
              [9.67, 7.63, 3.91, 4.18, 2.16, 8.32, 1.33, 6.11],
              [4.17, 6.97, 9.09, 8.94],
              [7.66, 7.07, 6.82, 8.33, 8.11, 4.72],
              [4.22, 6.74, 2.49, 6.77, 6.75, 5.97, 8.58],
              [3.34, 4.81, 4.87, 9.34, 5.57, 7.38],
              [4.46, 7.91, 4.84, 5.32, 2.08, 3.67, 8.81, 1.9],
              [4.08, 8.33, 2.66, 5.16, 8.04],
            ],
            backgroundColor: 'rgba(75, 192, 192,0.2)',
            borderColor: 'rgba(75, 192, 192,1)',
            borderWidth: 1,
            itemStyle: 'circle',
            itemBackgroundColor: 'rgba(75, 192, 192,1)',
            outlierBackgroundColor: 'rgba(75, 192, 192,1)',
            itemRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Scatter with Line Chart',
          },
          datalabels: {
            display: false,
          },
        },
      },
      type: 'boxplot',
    },
  },
};
