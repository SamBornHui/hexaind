import { HttpErrorResponse } from '@angular/common/http';
import { throwError } from 'rxjs';
import {
  CellStyleColumn,
  Column,
  DataColumn,
  DataType,
  Filter,
  IdNameData,
  IdNameParentNamesData,
  SimpleObject,
  SortInfo,
  TreeData,
  VizData,
} from '../components/models';

export function arraysEqual(arr1: any[], arr2: any[]) {
  // Check if lengths are different
  if (arr1.length !== arr2.length) {
    return false;
  }

  // Check if all elements at the same index are equal
  return arr1.every((value, index) => value === arr2[index]);
}

export function getClassNames(...classes: (string | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

const MAX_LABEL_LENGTH = 10;
export const truncateString = (label: string, maxLength = MAX_LABEL_LENGTH) => {
  if (label.length > maxLength) {
    return label.substring(0, maxLength) + '...';
  }
  return label;
};

export function parseCsv(id: string, csvText: string): VizData {
  const lines = csvText.split('\n').filter((line) => line.trim() !== ''); // Filter out empty lines
  if (lines.length < 2) {
    throw new Error('CSV must have at least a header row and one data row.');
  }
  const headers = lines[0].split(',').map((h) => h.trim());

  // Infer data types using the correct header row
  const columns: DataColumn[] = headers.map((header) => ({
    name: header,
    type: inferDataType(header, lines.slice(1, 100), headers), // sampling 100 rows
  }));
  // console.log('columns', columns);
  const rows: { [key: string]: any }[] = [];

  for (let i = 1; i < lines.length; i++) {
    const row = lines[i].split(',').map((r) => r.trim());
    if (row.length === headers.length) {
      const item: { [key: string]: any } = {};
      for (let j = 0; j < headers.length; j++) {
        item[headers[j]] = convertDataType(row[j], columns[j].type);
      }
      rows.push(item);
    }
  }

  return { dataset: { id }, columns, rows };
}

// Helper function to infer data type based on column values
function inferDataType(
  header: string,
  dataRows: string[],
  headers: string[],
): DataType {
  const columnIndex = headers.indexOf(header); // Get column index from headers array
  if (columnIndex === -1) {
    return 'string'; // Default to string if column not found
  }

  const values = dataRows
    .map((row) => {
      const cols = row.split(',');
      return cols[columnIndex] ? cols[columnIndex].trim() : null;
    })
    .filter((value) => value !== '' && value !== undefined && value !== null);

  // Check for empty values after filtering
  if (values.length === 0) {
    return 'string'; // Default to string if all values are empty
  }
  // If all values are valid numbers, infer as number
  if (values.every((value) => !isNaN(Number(value)))) {
    return 'number';
  }

  // Add more type inference logic (e.g., for dates) if needed

  // Default to string if no other type is inferred
  return 'string';
}

function convertDataType(value: string, type: DataType | undefined): any {
  if (value === '' || value === undefined || value === null) {
    return null;
  }
  switch (type) {
    case 'number':
      return Number(value);
    case 'date':
    // Add date parsing logic if needed. Example:
    // return new Date(value);
    default:
      return value;
  }
}

function checkFilter(filter: Filter, item: any, rowIndex?: number) {
  const { type, field, value, to = value } = filter;
  const targetValue = item[field];
  if (value == null || to == null) return true;
  switch (type) {
    case 'range':
      return targetValue >= value && targetValue <= to;
    case '>':
      return targetValue > value;
    case '<':
      return targetValue < value;
    case '=':
      return targetValue === value;
    case '!=':
      return targetValue !== value;
    case 'includes':
      return String(targetValue)
        .toLowerCase()
        .includes(String(value).toLowerCase());
    default:
      return true;
  }
}

export function filterAndSortData(
  data: VizData,
  filters: Filter[] = [],
  sortInfos: SortInfo[] = [],
  top = 0,
): VizData {
  if (filters.length === 0 && sortInfos.length === 0) return { ...data };
  let filteredItems = [...data.rows];

  if (filters && filters.length > 0) {
    const columnSet = new Set(data.columns.map((column) => column.name));
    filteredItems = filteredItems.filter((item, i) =>
      filters.every((filter) => {
        if (!columnSet.has(filter.field)) return true;
        return checkFilter(filter, item);
      }),
    );
  }
  if (top > 0) {
    filteredItems = filteredItems.slice(0, top);
  }
  filteredItems = sortData(filteredItems, sortInfos);
  return { ...data, rows: filteredItems };
}

export function sortData(items: any[], sortInfos: SortInfo[] = []) {
  if (sortInfos && sortInfos.length > 0) {
    items.sort((a, b) => {
      for (const sortInfo of sortInfos) {
        const { field, direction } = sortInfo;
        const aValue = a[field];
        const bValue = b[field];

        if (direction === 'none') {
          continue;
        }

        const isAsc = direction === 'asc';

        if (aValue === bValue) {
          continue;
        }

        if (aValue === null) {
          return isAsc ? -1 : 1;
        }
        if (bValue === null) {
          return isAsc ? 1 : -1;
        }

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return isAsc ? aValue - bValue : bValue - aValue;
        }
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return isAsc
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        }

        return 0;
      }
      return 0;
    });
  }
  return items;
}

export function getCellStyleByFilter(
  data: any,
  column: Column,
  rowIndex: number,
  cellStyleColumns: CellStyleColumn[],
): string {
  if (cellStyleColumns.length === 0) return '';
  let style = '';
  cellStyleColumns.forEach((cellStyleColumn: CellStyleColumn) => {
    const {
      type = 'cell',
      filter: { field },
      options: { backgroundColor = '', borderColor = '' },
    } = cellStyleColumn;
    if (
      type === 'cell' &&
      field === column.field &&
      checkFilter(cellStyleColumn.filter, data, rowIndex)
    ) {
      style = `border-color: ${borderColor}; background-color: ${backgroundColor}`;
    }
  });
  return style;
}

/*************** tree utils start **************/
export function flattenNestedArray(nestedArray: any[], level = 0): any[] {
  const flatArray = [];

  for (const item of nestedArray) {
    const hasChildren = item.children && item.children.length > 0;
    const newItem = {
      ...item,
      level,
      hasChildren,
      expanded: true,
    }; // Create a copy and add level
    delete newItem.children; // Remove the children property

    flatArray.push(newItem);

    if (item.children && item.children.length > 0) {
      flatArray.push(...flattenNestedArray(item.children, level + 1));
    }
  }

  return flatArray;
}

export function getLastChildrenOfNestedArray(
  nestedArray: any[],
  childrenFiledName: string = 'children',
  lastChildTypeFieldName: string = 'nodeType',
  lastChildTypeFieldValue: string = 'output',
): IdNameParentNamesData[] {
  const flatArray: IdNameParentNamesData[] = [];
  const itemSet = new Set<string>(); // Keep track of added items using their IDs

  function traverse(items: IdNameData[], parentNames: string[] = []) {
    items.forEach((item) => {
      const currentParentNames = [...parentNames]; // Create a copy
      currentParentNames.push(item.name || '');
      if (
        item[lastChildTypeFieldName]?.toLocaleLowerCase() ===
        lastChildTypeFieldValue.toLocaleLowerCase()
      ) {
        // Check if it is the last child and an output
        // Check if the item has already been added
        if (!itemSet.has(item.id)) {
          const parentNames = currentParentNames.slice(
            0,
            currentParentNames.length - 1,
          );
          flatArray.push({
            parentNames, // Exclude current item name from parents
            ...item,
          });
          itemSet.add(item.id); // Add the item's ID to the set
        }
      } else if (item[childrenFiledName]?.length > 0) {
        traverse(item[childrenFiledName], currentParentNames);
      }
    });
  }

  traverse(nestedArray);
  return flatArray;
}

export const getChildren = (
  items: (TreeData | SimpleObject)[],
  index: number,
) => {
  const item = items[index];
  const children = [];
  for (let i = index + 1; i < items.length; i++) {
    if (items[i].level <= item.level) {
      break;
    }
    children.push(items[i]);
  }
  return children;
};

export const collapseChildren = (
  childrenMap: Map<string, (TreeData | SimpleObject)[]>,
  item: TreeData | SimpleObject,
  items: (TreeData | SimpleObject)[],
  index: number,
  keyField = 'id',
) => {
  item.expanded = false;
  const children = getChildren(items, index);
  childrenMap.set(item[keyField], children);
  items.splice(index + 1, children.length);
};

export const collapseAll = (
  childrenMap: Map<string, (TreeData | SimpleObject)[]>,
  items: (TreeData | SimpleObject)[],
  keyField = 'id',
) => {
  items.forEach((item, index) => {
    collapseChildren(childrenMap, item, items, index, keyField);
  });
};

export const addChildren = (
  data: {
    children: TreeData[];
    parentId: string;
  },
  items: TreeData[],
  keyField = 'id',
) => {
  const { children, parentId } = data;
  const parentIndex = items.findIndex((item) => item[keyField] === parentId);
  if (parentIndex === -1) {
    return;
  }
  const parent = items[parentIndex];
  parent.loading = false;
  parent.expanded = true;
  const childrenIndex = parentIndex + 1;
  items.splice(childrenIndex, 0, ...children);
  items[parentIndex] = parent;
  return items;
};

/*************** tree utils end **************/

export const updateItemsByPage = (
  items: any[] = [],
  pageItems: any[],
  offset: number,
): any[] => {
  const updatedItems = items.slice();
  pageItems.forEach((item, index) => (updatedItems[offset + index] = item));
  return updatedItems;
};

export function handleHttpError(error: HttpErrorResponse) {
  console.error('An error occurred:', error);

  let errorMessage = 'Something went wrong; please try again later.';
  if (error.error.detail?.message) {
    errorMessage = `Error: ${error.error.detail.message}`;
  } else if (error.error instanceof ErrorEvent) {
    // Client-side error
    errorMessage = `Error: ${error.error.message}`;
  } else {
    // Server-side error
    errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
  }

  return throwError(() => errorMessage);
}
