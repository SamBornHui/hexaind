import { BubbleDataPoint } from 'chart.js';

interface NumberConfig {
  count?: number;
  rmin?: number;
  rmax?: number;
  min?: number;
  max?: number;
  section?: number;
  from?: number[];
  decimals?: number;
  continuity?: number;
}

var _seed = Date.now();

export function rand(min = 0, max = 0) {
  min = valueOrDefault(min, 0);
  max = valueOrDefault(max, 0);
  _seed = (_seed * 9301 + 49297) % 233280;
  return min + (_seed / 233280) * (max - min);
}

const valueOrDefault = (value: any, defaultValue: any) => {
  return value == null ? defaultValue : value;
};

export function numbers(config: NumberConfig) {
  var cfg = config || {};
  var min = valueOrDefault(cfg.min, 0);
  var max = valueOrDefault(cfg.max, 100);
  var from = valueOrDefault(cfg.from, []);
  var count = valueOrDefault(cfg.count, 8);
  var decimals = valueOrDefault(cfg.decimals, 8);
  var continuity = valueOrDefault(cfg.continuity, 1);
  var dfactor = Math.pow(10, decimals) || 0;
  var data = [];
  var i, value;

  for (i = 0; i < count; ++i) {
    value = (from[i] || 0) + rand(min, max);
    if (rand() <= continuity) {
      data.push(Math.round(dfactor * value) / dfactor);
    } else {
      data.push(null);
    }
  }
  return data;
}

export function points(config: NumberConfig) {
  const xs = numbers(config);
  const ys = numbers(config);
  return xs.map((x, i) => ({ x, y: ys[i] })) as BubbleDataPoint[];
}

export function bubbles(config: NumberConfig) {
  return points(config).map((pt) => {
    pt.r = rand(config.rmin, config.rmax);
    return pt;
  });
}

const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

export function months(config: NumberConfig) {
  var cfg = config || {};
  var count = cfg.count || 12;
  var section = cfg.section;
  var values = [];
  var i, value;

  for (i = 0; i < count; ++i) {
    value = MONTHS[Math.ceil(i) % 12];
    values.push(value.substring(0, section));
  }

  return values;
}

export const getRandomNumber = (min = 0, max = 99) =>
  Math.floor(Math.random() * (max - min + 1)) + min;

export const delay = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));
