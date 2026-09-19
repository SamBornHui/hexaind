import {
  BoxAndWiskers,
  BoxPlotController,
} from '@sgratzl/chartjs-chart-boxplot';
import {
  BubbleDataPoint,
  CategoryScale,
  Chart,
  ChartData,
  ChartOptions,
  ChartType,
  LinearScale,
  Point,
  PointStyle,
  registerables,
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { truncateString } from '../../utils/utils';
import {
  ChartConfig,
  Column,
  DataColumn,
  DatasetData,
  VizConfig,
  VizData,
  VizDataColumn,
  VizOptions,
  VizType,
} from '../models';

/**
 *
data:
   {
      labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
      datasets: [
        {
          label: 'Sales',
          data: [12, 19, 3, 5, 2, 3, 7],
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
        },
      ],
    }
options:
    {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    }
 * @param el
 * @param data
 * @param options
 */
export const renderChart = (
  el: HTMLCanvasElement,
  data: ChartData,
  options: ChartOptions,
  type: ChartType = 'bar',
): Chart => {
  Chart.register(
    ...registerables,
    ChartDataLabels,
    BoxPlotController,
    BoxAndWiskers,
    LinearScale,
    CategoryScale,
  );
  return new Chart(el, {
    type,
    data,
    options,
  });
};

export const getColumnIndexMap = (columns: string[]) => {
  const map = new Map<string, number>();
  columns.forEach((name, index) => {
    map.set(name, index);
  });
  return map;
};

export const getColumnsByData = (items: { [key: string]: any }[]): Column[] =>
  items[0]
    ? Object.keys(items[0]).map((key) => ({ name: key, field: key }))
    : [];

export const convertVizData = (data: DatasetData): VizData => {
  const { id, rows, columns } = data;
  const items = rows.map((item) => {
    const row: any = {};
    data.columns.forEach(({ name }: DataColumn, i) => {
      row[name] = item[i];
    });
    return row;
  });
  return {
    dataset: { id },
    columns,
    rows: items,
  };
};

const CHART_COLORS = {
  blue: '54, 162, 235',
  red: '255, 99, 132',
  green: '75, 192, 192',
  purple: '153, 102, 255',
  orange: '255, 159, 64',
  grey: '201, 203, 207',
  pink: '255, 192, 203',
  brown: '165, 42, 42',
  cyan: '0, 255, 255',
  yellow: '255, 205, 86',
  lime: '0, 255, 0',
  teal: '0, 128, 128',
  navy: '0, 0, 128',
  olive: '128, 128, 0',
  maroon: '128, 0, 0',
  silver: '192, 192, 192',
  gold: '255, 215, 0',
  magenta: '255, 0, 255',
  indigo: '75, 0, 130',
  plum: '221, 160, 221',
  orchid: '218, 112, 214',
  salmon: '250, 128, 114',
  coral: '255, 127, 80',
  turquoise: '64, 224, 208',
  aquamarine: '127, 255, 212',
  violet: '238, 130, 238',
  wheat: '245, 222, 179',
  crimson: '220, 20, 60',
  khaki: '240, 230, 140',
  lavender: '230, 230, 250',
};

export const getRGBA = (
  color: keyof typeof CHART_COLORS = 'blue',
  opacity = 1,
) => {
  const rgb = CHART_COLORS[color];
  return `rgba(${rgb},${opacity})`;
};

export const getRGBAByIndex = (colorIndex: number = 0, opacity = 1) => {
  const colors = Object.keys(CHART_COLORS);
  colorIndex = colorIndex % colors.length;
  return getRGBA(colors[colorIndex] as keyof typeof CHART_COLORS, opacity);
};

export const getColors = () =>
  Object.keys(CHART_COLORS).map((key) =>
    getRGBA(key as keyof typeof CHART_COLORS),
  );

const getPoint = (fieldX: string, fieldY: string, data: any): Point => ({
  x: data[fieldX],
  y: data[fieldY],
});

const getBubble = (
  fieldX: string,
  fieldY: string,
  fieldR = '',
  data: any,
): BubbleDataPoint => ({
  ...getPoint(fieldX, fieldY, data),
  r: fieldR ? data[fieldR] || 1 : 1,
});

export const getPoints = (fieldX: string, fieldY: string, items: any[]) =>
  items.map((item) => getPoint(fieldX, fieldY, item));

export const getBubbles = (
  fieldX: string,
  fieldY: string,
  fieldR = '',
  items: any[],
) => items.map((item) => getBubble(fieldX, fieldY, fieldR, item));

const getPointStyles = (
  pointStyle: PointStyle = 'circle',
  pointBorderColor: string,
  pointBackgroundColor: string,
) => ({
  pointStyle,
  pointRadius: pointStyle === 'circle' ? 3 : 5,
  pointBorderColor,
  pointBackgroundColor,
});
/**
 * bar / line can have only one x label column and multiple datasets
 */

export const getChartConfig = (
  vizType: VizType,
  data: VizData = { dataset: { id: '' }, columns: [], rows: [] },
  vizConfig: VizConfig = {},
) => {
  switch (vizType) {
    case 'line':
    case 'bar':
      return getBasicChartConfig(data.rows, vizConfig, vizType);
    case 'boxplot':
      return getBoxplotConfig(data.rows, vizConfig, vizType);
    case 'pie':
      return getPieChartConfig(data.rows, vizConfig);
    case 'scatter':
      return getScatterChartConfig(data.rows, vizConfig);
    case 'table':
      break;
  }
  return {};
};

const getDefaultChartOptions = (
  hasDataLabel = false,
  plugins: any = {},
): ChartOptions => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    datalabels: {
      display: hasDataLabel,
    },
    ...plugins,
  },
});

const getBasicChartConfig = (
  data: { [key: string]: any }[],
  vizConfig: VizConfig = {},
  type: ChartType,
) => {
  const chartData: ChartData = { labels: [], datasets: [] };
  let chartConfig: ChartConfig = {};
  if (data && vizConfig.labelDataColumns) {
    const { label, dataColumns = [] } = vizConfig.labelDataColumns;
    data.forEach((item) => {
      dataColumns.forEach((dataColumn, i) => {
        const { type, field, options = {} } = dataColumn;
        if (label && i === 0) {
          chartData.labels?.push(item[label]);
        }
        if (field) {
          const backgroundColor =
            options.backgroundColor || getRGBAByIndex(i, 0.2);
          const borderColor = options.borderColor || getRGBAByIndex(i);
          const dataset = chartData.datasets[i] || {
            ...getPointStyles(
              options?.pointStyle,
              borderColor,
              backgroundColor,
            ),
            label: field,
            backgroundColor,
            borderColor,
            borderWidth: 1,
            data: [],
            type: options.type || type,
          };
          dataset.data.push(item[field]);
          chartData.datasets[i] = dataset;
        }
      });
    });
    chartConfig = {
      data: chartData,
      options: {
        ...getDefaultChartOptions(vizConfig.hasDataLabel),
        scales: {
          x: {
            ticks: {
              callback: function (value, _index, _values) {
                return truncateString(this.getLabelForValue(+value));
              },
            },
          },
        },
      },
      type,
    };
  }
  return chartConfig;
};

/**
 *
 * @param groupByColumn
 * @param dataColumns
 * @param data
 * @returns
 processDataForBoxplot('state', ['iPhone', 'iPad', 'iMac'], [....])
 *
{
  labels: ['CA', 'WA', ...],
  datasets: [
    {
      label: 'iPhone',
      //      CA        WA       XX
      data: [[12, 19], [12, 19], ...],
    },
    {
      label: 'iPad',
      data: [[12, 19], [12, 19]],
    },
    {
      label: 'iMac',
      data: [[12, 19], [12, 19]],
    },
  ],
}
 */
const getBoxplotData = (
  groupByColumn: string,
  dataColumns: VizDataColumn[],
  data: { [key: string]: any }[],
) => {
  const datasets: any[] = [];
  //          CA, WA,
  // iPhone, [12, 19, ...], iPad, [12, 19, ...], iMac, [12, 19]
  const labelSet = new Set<string>();
  data.forEach((item) => {
    labelSet.add(item[groupByColumn]);
  });
  const labels = Array.from(labelSet);
  const fieldLabelValuesMap = new Map<string, Map<string, any[]>>();
  const fields = dataColumns.map((col) => col.field);
  data.forEach((item) => {
    fields.forEach((field) => {
      const labelValuesMap =
        fieldLabelValuesMap.get(field) || new Map<string, any[]>(); // CA, [12, 19]
      const labelValues = labelValuesMap.get(item[groupByColumn]) || [];
      labelValues.push(item[field]);
      labelValuesMap.set(item[groupByColumn], labelValues);
      fieldLabelValuesMap.set(field, labelValuesMap);
    });
  });
  dataColumns.forEach((col, i) => {
    const data = labels.map((label) => {
      return fieldLabelValuesMap.get(col.field)?.get(label) || [];
    });
    const itemStyle = col.options?.pointStyle || 'circle';
    const backgroundColor =
      col.options?.backgroundColor || getRGBAByIndex(i, 0.2);
    const borderColor = col.options?.borderColor || getRGBAByIndex(i);
    datasets.push({
      label: col.field,
      data,
      backgroundColor,
      borderColor,
      borderWidth: 1,
      itemStyle,
      itemBackgroundColor: borderColor,
      outlierBackgroundColor: borderColor,
      itemRadius: itemStyle === 'circle' ? 3 : 5,
    });
  });
  return { labels, datasets };
};

const getBoxplotConfig = (
  data: { [key: string]: any }[],
  vizConfig: VizConfig = {},
  type: ChartType,
) => {
  let chartData: ChartData;
  let chartConfig: ChartConfig = {};
  if (data && vizConfig.labelDataColumns) {
    const { label, dataColumns = [] } = vizConfig.labelDataColumns;
    chartData = getBoxplotData(label, dataColumns, data);
    chartConfig = {
      data: chartData,
      options: {
        ...getDefaultChartOptions(vizConfig.hasDataLabel),
        scales: {
          x: {
            ticks: {
              callback: function (value, _index, _values) {
                return truncateString(this.getLabelForValue(+value));
              },
            },
          },
        },
      },
      type,
    };
  }
  return chartConfig;
};

const getPieChartConfig = (
  data: { [key: string]: any }[],
  vizConfig: VizConfig = {},
) => {
  const chartData: ChartData = { labels: [], datasets: [] };
  let chartConfig: ChartConfig = {};
  if (data && vizConfig.labelDataColumns) {
    const { label, dataColumns = [] } = vizConfig.labelDataColumns;
    data.forEach((item) => {
      dataColumns.forEach((dataColumn, i) => {
        const { field } = dataColumn;
        if (label && i === 0) {
          chartData.labels?.push(item[label]);
        }
        if (field) {
          const dataset = chartData.datasets[i] || {
            label: field,
            backgroundColor: getColors(),
            borderColor: '#fff',
            borderWidth: 1,
            data: [],
          };
          dataset.data.push(item[field]);
          chartData.datasets[i] = dataset;
        }
      });
    });
    chartConfig = {
      data: chartData,
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
            formatter: (value: number, context: any) => {
              let sum = 0;
              const dataArr = context.chart.data.datasets[0].data;
              dataArr.forEach((data: number) => {
                sum += +data;
              });
              const percentage = ((value * 100) / sum).toFixed(2) + '%';
              return percentage;
            },
          },
        },
      },
      type: 'pie',
    };
  }
  return chartConfig;
};

const getScatterChartConfig = (
  items: { [key: string]: any }[],
  vizConfig: VizConfig = {},
) => {
  const chartData: ChartData = { labels: [], datasets: [] };
  let chartConfig: ChartConfig = {};
  if (items && vizConfig.labelBubbleColumns) {
    items.forEach((item) => {
      vizConfig.labelBubbleColumns?.forEach((labelBubbleColumn, i) => {
        const {
          label,
          bubbleColumn: { x, y, r },
          options,
        } = labelBubbleColumn;
        const backgroundColor =
          options?.backgroundColor || getRGBAByIndex(i, 0.2);
        const borderColor = options?.borderColor || getRGBAByIndex(i);
        const dataset = chartData.datasets[i] || {
          ...getPointStyles(options?.pointStyle, borderColor, backgroundColor),
          label,
          backgroundColor,
          borderColor,
          data: [],
          type: options?.type || 'scatter',
        };
        dataset.data.push(getBubble(x, y, r, item));
        chartData.datasets[i] = dataset;
      });
    });
    // console.log('scatter chartData', chartData);
    chartConfig = {
      data: chartData,
      options: {
        ...getDefaultChartOptions(vizConfig.hasDataLabel),
      },
      type: 'scatter',
    };
  }
  return chartConfig;
};

export const initVizOptions = (options: VizOptions = {}, i = 0) => {
  if (!options.backgroundColor) {
    options.backgroundColor = getRGBAByIndex(i, 0.2);
  }
  if (!options.borderColor) {
    options.borderColor = getRGBAByIndex(i);
  }
  if (!options.pointStyle) {
    options.pointStyle = 'circle';
  }
  return options;
};
