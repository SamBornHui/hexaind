import { ElementRef } from '@angular/core';
import { WidgetControl } from './controls/widget-control/widget-control';

import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { FileType, Widget, WidgetType } from './models/workflow-models';
import { environment } from '../environments/environment';
import { WidgetClientType } from './pages/workflow-designer/client-tags';
import { Project } from './models/project-models';
import { ProblemType } from 'src/app/models/workflow-models';

export interface DirectoryItem {
  name: string;
  type: string; // 'file' or 'folder'
  path: string;
  size: string;
  children?: DirectoryItem[];
}

enum WidgetOutputType {
  Tabular = 'Tabular',
  None = 'None',
  PassThrough = 'PassThrough', // loop start and end
}

export class Utils {
  private static readonly CHUNK_SIZE = 1024 * 1024; // 1 MB per chunk

  static GetHttpResponseError(error: HttpErrorResponse): string {
    if (error.error?.detail?.message) {
      return error.error.detail.message;
    }
    if (Array.isArray(error.error?.detail) && error.error.detail.length > 0) {
      return error.error.detail[0].msg ?? JSON.stringify(error.error.detail);
    }
    return 'An unknown error has occurred.';
  }

  static GetToolTiplabelByType(
    widgetType: WidgetType,
    widgetClientType: WidgetClientType,
  ) {
    switch (widgetType) {
      case WidgetType.LOOP_END:
        return 'Loop End';
      case WidgetType.LOOP_START:
        return 'Loop Start';
      case WidgetType.APPEND:
        return 'Append';
      case WidgetType.FILTER:
        return 'Filter';
      case WidgetType.DROP_MISSING:
        return 'Drop Missing';
      case WidgetType.RENAME_COLUMNS:
        return 'Rename Columns';
      case WidgetType.CONFIG_FILE:
        return 'Config File';
      case WidgetType.JOIN:
        return 'Join';
      case WidgetType.PIVOT:
        return 'Pivot';
      case WidgetType.MOBO:
        return 'MOBO';
      case WidgetType.RESCALE:
        return 'Rescale';
      case WidgetType.POST_RESCALE:
        return 'Post Rescale';
      case WidgetType.Feature_Engineering:
        return 'Feature Engineering';
      case WidgetType.SAVE:
        return 'Save';
      case WidgetType.CUSTOM_CODE:
        return 'Custom Code';
      case WidgetType.DECISION:
        return 'Decision';
      case WidgetType.PYTHON:
        return 'Python';
      case WidgetType.UNION:
        return 'Union';
      case WidgetType.THERMOCALC:
        return 'ThermoCalc';
      case WidgetType.DROP_COLUMNS:
        return 'Drop Columns';
      case WidgetType.DATATYPE_CONVERSION:
        return 'Datatype Conversion'
    }

    switch (widgetClientType) {
      case WidgetClientType.CSVFile:
        return 'CSV File';
      case WidgetClientType.ExcelFile:
        return 'Excel File';
      case WidgetClientType.BigQuery:
        return 'Big Query';
      case WidgetClientType.ImageFile:
        return 'Image File';
      case WidgetClientType.Start:
        return 'Start Widget';
      case WidgetClientType.End:
        return 'End Widget';
      case WidgetClientType.ParquetFile:
        return 'Parquet File';
    }

    return widgetType.toString();
  }

  static GetWidgetOutputType(widget: Widget): string | null {
    // TBD (Mike): case WidgetType.TRANSFORM
    // TBD (Mike): case WidgetType.LightGBM
    switch (widget.type) {
      case WidgetType.LOOP_END:
      case WidgetType.LOOP_START:
        return WidgetOutputType.PassThrough;
      case WidgetType.APPEND:
      case WidgetType.FILTER:
      case WidgetType.DROP_MISSING:
      case WidgetType.RENAME_COLUMNS:
      case WidgetType.DATATYPE_CONVERSION:
      case WidgetType.CONFIG_FILE:
      case WidgetType.JOIN:
      case WidgetType.PIVOT:
      case WidgetType.MOBO:
      case WidgetType.RESCALE:
      case WidgetType.POST_RESCALE:
      case WidgetType.Feature_Engineering:
      case WidgetType.ACTIVE_LEARNING:
      case WidgetType.CUSTOM_CODE:
      case WidgetType.GPR:
      case WidgetType.MPR:
      case WidgetType.AUTOML:
      case WidgetType.LGBM:
      case WidgetType.LINEAR_REGRESSION:
      case WidgetType.RF:
      case WidgetType.NNFASTAI:
      case WidgetType.NN_TORCH:
      case WidgetType.XGBOOST:
      case WidgetType.CATBOOST:
      case WidgetType.EXTRA_TREES:
      case WidgetType.KNEIGHBORS:
      case WidgetType.ARIMA:
      case WidgetType.PREDICTION:
      case WidgetType.SVM:
      case WidgetType.GPC:
      case WidgetType.THERMOCALC:
      case WidgetType.DROP_COLUMNS:
      case WidgetType.IMAGE_DATASET:
      case WidgetType.REGION_PROPERTY:
      case WidgetType.IMAGE_SPATIAL_STATISTICS:
      case WidgetType.TEXT_DATA:
        return WidgetOutputType.Tabular;
      case WidgetType.SAVE:
        return WidgetOutputType.None;
    }

    switch (widget.client_tags.ClientType) {
      case WidgetClientType.CSVFile:
      case WidgetClientType.ExcelFile:
      case WidgetClientType.BigQuery:
      case WidgetClientType.ParquetFile:
        return WidgetOutputType.Tabular;
    }

    return null;
  }

  public static CalculateColumns(parentWidth: number): number {
    const flexPercentage = 20; // Replace this with your actual fxFlex value, without the '%'
    const gutterSize = 20; // Adjust if different

    // Calculate the width of one tile based on the fxFlex percentage
    const tileWidth = parentWidth * (flexPercentage / 100);

    // Initially assume you can fit one tile without any gutters
    let numberOfGutters = 0;

    // Calculate available width deducting gutters as we add more tiles
    let availableWidth = parentWidth;
    let numberOfColumns = 0;

    while (availableWidth >= tileWidth) {
      numberOfColumns++; // Add a tile
      availableWidth -= tileWidth; // Deduct its width from available space

      // Add space for a gutter if more tiles can fit
      if (availableWidth >= gutterSize + tileWidth) {
        availableWidth -= gutterSize; // Deduct gutter space only if another tile can fit
        numberOfGutters++;
      }
    }

    // Now numberOfColumns contains the total count of columns that can fit
    return numberOfColumns;
  }

  static GetNamedOutput(widget: Widget, projectName: string): string | null {
    let dataType: string | null = Utils.GetWidgetOutputType(widget);
    if (!dataType) {
      return null;
    }
    return projectName + '_' + widget.name + '_' + dataType;
  }

  static async UploadFileWithMinimumTwoLines(
    file: File,
    percentage: number,
    chunkSize: number = 1024 * 1024,
  ): Promise<void> {
    const totalSize = file.size;
    let targetSize = Math.ceil(totalSize * (percentage / 100));
    let offset = 0;

    // Function to find the end of the second line
    const findSecondLineEnd = async () => {
      return new Promise<number>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function (event) {
          const content = event.target!.result as string;
          const lines = content.split('\n');
          if (lines.length >= 2) {
            resolve(content.indexOf('\n', content.indexOf('\n') + 1) + 1);
          } else {
            reject(new Error('File does not contain two lines.'));
          }
        };
        reader.onerror = () => reject(new Error('Error reading file.'));
        reader.readAsText(file.slice(0, Math.min(4096, totalSize)));
      });
    };

    // Upload chunk function
    const uploadChunk = async (chunk: Blob, chunkNumber: number) => {
      const formData = new FormData();
      formData.append('file', chunk, file.name);
      formData.append('chunkNumber', chunkNumber.toString());

      try {
        const response = await fetch(
          `${environment.apiUrl}/datasets/upload-chunk`,
          {
            method: 'POST',
            body: formData, // formData should include the file chunk and chunk number
            // headers, authentication, etc., if needed
          },
        );

        // Optional: Handle the response
        const result = await response.json();
      } catch (error) {
        console.error('Upload failed', error);
        throw error;
      }
    };

    // Ensure at least two lines are included in the upload
    targetSize = Math.max(targetSize, await findSecondLineEnd());

    while (offset < targetSize) {
      const nextChunkEnd = Math.min(offset + chunkSize, targetSize, totalSize);
      let chunkEnd = nextChunkEnd;

      if (chunkEnd < totalSize) {
        // Read ahead to ensure we don't cut a line
        const readAhead = new FileReader();
        readAhead.onload = function (event) {
          const content = event.target!.result as string;
          const newlineIndex = content.indexOf('\n');
          if (newlineIndex !== -1) {
            chunkEnd = offset + chunkSize + newlineIndex + 1;
          }
        };
        readAhead.readAsText(file.slice(nextChunkEnd, nextChunkEnd + 1024)); // Read ahead by 1KB
        await new Promise((resolve) => (readAhead.onloadend = resolve));
      }

      const chunk = file.slice(offset, chunkEnd);
      await uploadChunk(chunk, offset / chunkSize);
      offset = chunkEnd;
    }
  }

  static LoadTabularFileByPercentage(
    file: File,
    percentage: number,
  ): Promise<string[]> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      const totalSize = file.size;
      let targetSize = Math.ceil(totalSize * (percentage / 100));
      let accumulatedText = '';
      let lines: string[] = [];
      let offset = 0;

      // Define a minimum chunk size to handle very small files
      const minChunkSize = 512; // 512 bytes
      // Calculate an initial chunk size as a fraction of the target size
      let chunkSize = Math.max(minChunkSize, targetSize / 10);

      // Ensure chunk size is not greater than the target size
      chunkSize = Math.min(chunkSize, targetSize);

      // Ensure at least two lines are read (for CSV header and first data line)
      const readAtLeastTwoLines = () => {
        return new Promise((resolve) => {
          const tempReader = new FileReader();
          tempReader.onload = function (event) {
            const content = event.target!.result as string;
            const lines = content.split('\n');
            if (lines.length >= 2) {
              resolve(content.indexOf('\n', content.indexOf('\n') + 1) + 1); // Find the second newline
            } else {
              resolve(content.length); // If less than two newlines, return the total length
            }
          };
          tempReader.readAsText(file.slice(0, Math.min(4096, totalSize))); // Read up to 4KB to find two newlines
        });
      };

      readAtLeastTwoLines().then((minimumSize) => {
        targetSize = Math.max(targetSize, minimumSize as number);
        chunkSize = Math.min(chunkSize, targetSize);

        reader.onload = function (event) {
          const textChunk = event.target!.result as string;
          accumulatedText += textChunk;
          const tempLines = accumulatedText.split('\n');

          // If we're in the middle of a line, leave the last line in the buffer
          if (!accumulatedText.endsWith('\n')) {
            accumulatedText = tempLines.pop() || '';
          } else {
            accumulatedText = '';
          }

          lines = lines.concat(tempLines);

          if (offset >= targetSize || offset >= totalSize) {
            resolve(lines); // Resolve with complete lines
            return;
          }

          readNextChunk();
        };

        reader.onerror = function (error) {
          reject(error);
        };

        const readNextChunk = () => {
          const nextChunkSize = Math.min(
            chunkSize,
            totalSize - offset,
            targetSize - offset,
          );
          const blob = file.slice(offset, offset + nextChunkSize);
          reader.readAsText(blob);
          offset += nextChunkSize;
        };

        readNextChunk();
      });
    });
  }

  static GetFileType(extension: string): FileType {
    // Extract the file extension

    // Determine the file type based on the extension
    switch (extension) {
      case 'csv':
        return FileType.CSV;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
        return FileType.Image;
      case 'parquet':
        return FileType.Parquet;
      case 'pdf':
        return FileType.PDF;
      default:
        throw new Error('Unsupported file type');
    }
  }

  static GetCsvColumnCount(csvString: string) {
    const lines = csvString.split('\n');
    const firstLine = lines[0];
    const columns = firstLine.split(','); // Use the appropriate delimiter if not comma
    return columns.length;
  }

  static DetermineTypesFromCsv(
    csvFile: string,
  ): { header: string; type: string; checked: true }[] {
    // Split the CSV string into lines
    const lines = csvFile.split(/\r?\n/);

    // Ensure there are at least two lines (headers and at least one row of data)
    if (lines.length < 2) {
      return [];
    }

    // Extract headers from the first line
    const headers = lines[0].split(',');

    // Extract data from the second line
    const data = lines[1].split(',');

    // Map headers to their types
    return headers.map((header, index) => {
      // Check if the corresponding value in the data row can be converted to a number
      const type = isNaN(Number(data[index])) ? 'Categorical' : 'Numerical';
      const isChecked: boolean = true;
      return { header, type, checked: true };
    });
  }

  static ExtractCsvColumnHeaders(csvString: string): string[] {
    // Split the CSV string into lines
    const lines = csvString.split(/\r?\n/);

    // Check if there are any lines to process
    if (lines.length === 0) {
      return [];
    }

    // Take the first line (assuming it contains headers)
    const headersLine = lines[0];

    // Split the headers line into individual column names
    const headers = headersLine.split(',');

    return headers;
  }

  static GenerateGuid(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0,
          v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      },
    );
  }

  static LineIntersectsLine(
    l1p1: { x: number; y: number },
    l1p2: { x: number; y: number },
    l2p1: { x: number; y: number },
    l2p2: { x: number; y: number },
  ): boolean {
    const det =
      (l1p1.x - l1p2.x) * (l2p1.y - l2p2.y) -
      (l1p1.y - l1p2.y) * (l2p1.x - l2p2.x);
    if (det === 0) return false;

    const lambda =
      ((l2p1.y - l2p2.y) * (l2p1.x - l1p1.x) +
        (l2p2.x - l2p1.x) * (l2p1.y - l1p1.y)) /
      det;
    const gamma =
      ((l1p1.y - l1p2.y) * (l2p1.x - l1p1.x) +
        (l1p2.x - l1p1.x) * (l2p1.y - l1p1.y)) /
      det;

    return 0 < lambda && lambda < 1 && 0 < gamma && gamma < 1;
  }

  static LineIntersectsRect(
    p1: { x: number; y: number },
    p2: { x: number; y: number },
    widgetControl: WidgetControl,
  ): boolean {
    const topLeft = {
      x: widgetControl.GetPositionX(),
      y: widgetControl.GetPositionY(),
    };
    const topRight = {
      x: widgetControl.GetPositionX() + widgetControl.GetWidth(),
      y: widgetControl.GetPositionY(),
    };
    const bottomLeft = {
      x: widgetControl.GetPositionX(),
      y: widgetControl.GetPositionY() + widgetControl.GetHeight(),
    };
    const bottomRight = {
      x: widgetControl.GetPositionX() + widgetControl.GetWidth(),
      y: widgetControl.GetPositionY() + widgetControl.GetHeight(),
    };

    return (
      Utils.LineIntersectsLine(p1, p2, topLeft, topRight) ||
      Utils.LineIntersectsLine(p1, p2, topRight, bottomRight) ||
      Utils.LineIntersectsLine(p1, p2, bottomLeft, bottomRight) ||
      Utils.LineIntersectsLine(p1, p2, topLeft, bottomLeft)
    );
  }

  static FormatFileSize(fileSize: number | null): string {
    if (!fileSize) {
      return '0';
    }
    const sizeInMB = fileSize / 1048576; // 1 MB in bytes
    if (sizeInMB < 1) {
      // If size is less than 1 MB, show in bytes with commas
      return fileSize.toLocaleString() + ' B';
    } else {
      // If size is 1 MB or more, convert to MB, add commas, and round to 2 decimal places
      return sizeInMB.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' MB';
    }
  }

  static ValidateFileName(fileName: string | null): number {
    // Define invalid characters - these might vary based on the operating system
    const invalidChars = /[<>:"/\\|?*\x00-\x1F]/g;

    if (!fileName) {
      return 0;
    }

    // Check for invalid characters in the filename
    if (invalidChars.test(fileName)) {
      return -1;
    }

    // Check for reserved filenames and length constraints
    const reservedNames = [
      'CON',
      'PRN',
      'AUX',
      'NUL',
      'COM1',
      'COM2',
      'COM3',
      'COM4',
      'COM5',
      'COM6',
      'COM7',
      'COM8',
      'COM9',
      'LPT1',
      'LPT2',
      'LPT3',
      'LPT4',
      'LPT5',
      'LPT6',
      'LPT7',
      'LPT8',
      'LPT9',
    ];
    const nameWithoutExtension = fileName.split('.')[0].toUpperCase();
    if (reservedNames.includes(nameWithoutExtension)) {
      return -2;
    }

    if (fileName.length > 40) {
      return -3;
    }

    // White spcae in file name not allowed.
    if (/\s/.test(fileName)) {
      return -4;
    }
    // If all checks pass, the filename is valid
    return 1;
  }

  static ArrayBufferToString(buffer: ArrayBuffer) {
    let decoder = new TextDecoder('utf-8');
    return decoder.decode(buffer);
  }

  static ConvertBytesToString(byteArray: Uint8Array) {
    let decoder = new TextDecoder();
    let text = decoder.decode(byteArray);
    return text;
  }

  static ConvertFileContentToBytes(
    fileContent: ArrayBuffer | string,
  ): Uint8Array | null {
    let byteArray: Uint8Array | null = null;

    if (typeof fileContent === 'string') {
      // If the file content is a string, you may need to encode it to bytes.
      // You can use TextEncoder to do that.
      const textEncoder = new TextEncoder();
      byteArray = textEncoder.encode(fileContent);
    } else if (fileContent instanceof ArrayBuffer) {
      // If the file content is already in ArrayBuffer format (for binary files),
      // you can directly work with the bytes.
      byteArray = new Uint8Array(fileContent);
    }
    return byteArray;
  }

  // Determine if mouse X & Y intersects an arrow drawon the canvas.
  static IsNearLine(
    mouseX: number,
    mouseY: number,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    tolerance: number,
  ): boolean {
    // Calculate the distance from the point to the line
    let dist =
      Math.abs((y2 - y1) * mouseX - (x2 - x1) * mouseY + x2 * y1 - y2 * x1) /
      Math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2);

    if (dist < tolerance) {
      // Check if the point is between the start and end points of the line segment
      let dotproduct = (mouseX - x1) * (x2 - x1) + (mouseY - y1) * (y2 - y1);
      if (dotproduct < 0) return false;

      let squaredlengthba = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
      if (dotproduct > squaredlengthba) return false;

      return true;
    }
    return false;
  }

  static isMouseNearLine(
    ctx: CanvasRenderingContext2D,
    px: number,
    py: number,
    ax: number,
    ay: number,
    bx: number,
    by: number,
    tolerance: number,
  ): boolean {
    const lineMag = Math.sqrt((bx - ax) ** 2 + (by - ay) ** 2);
    if (lineMag === 0) return false;

    const u =
      ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / (lineMag * lineMag);
    const nearestX = ax + u * (bx - ax);
    const nearestY = ay + u * (by - ay);
    const dist = Math.sqrt((px - nearestX) ** 2 + (py - nearestY) ** 2);

    // Use the passed ctx to draw the circle for debugging
    ctx.beginPath();
    ctx.arc(nearestX, nearestY, 3, 0, 2 * Math.PI, false);
    ctx.fillStyle = 'red';
    ctx.fill();

    const verticalBuffer = 5;
    const adjustedDist = Math.abs(dist - verticalBuffer);
    return adjustedDist <= tolerance && u >= 0 && u <= 1;
  }

  static IsPointInRect(
    canvas: ElementRef<HTMLCanvasElement> | null,
    x: number,
    y: number,
    widgetControl: WidgetControl,
  ): boolean {
    const canvasEl: HTMLCanvasElement = canvas!.nativeElement;
    const canvasRect = canvasEl.getBoundingClientRect();
    var clickX = x - canvasRect.left;
    var clickY = y - canvasRect.top;

    return (
      clickX >= widgetControl.GetPositionX() &&
      clickX <= widgetControl.GetPositionX() + widgetControl.GetWidth() &&
      clickY >= widgetControl.GetPositionY() &&
      clickY <= widgetControl.GetPositionY() + widgetControl.GetHeight()
    );
  }

  static formatDateTime(dateString: string): string {
    const date = new Date(dateString);

    // Pad the month and day with a zero if they are single digit
    const pad = (num: number) => num.toString().padStart(2, '0');

    // Extract the parts of the date
    const month = pad(date.getMonth() + 1); // getMonth() returns 0-11
    const day = pad(date.getDate());
    const year = date.getFullYear().toString().slice(-2); // Last two digits of the year

    // Format the time
    let hours = date.getHours();
    const minutes = pad(date.getMinutes());
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'

    return `${month}/${day}/${year} ${pad(hours)}:${minutes} ${ampm}`;
  }

  public static TimeSince(created_at: Date | string): string {
    const date = new Date(created_at);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    let interval = seconds / 31536000; // Number of seconds in a year

    if (interval === 1) {
      return `Last run 1 year ago`;
    } else if (interval > 1) {
      return `Last run ${Math.floor(interval)} years ago`;
    }

    interval = seconds / 2592000; // Number of seconds in a month
    if (interval > 1) {
      if (interval === 1) {
        return `Last run 1 month ago`;
      } else {
        return `Last run ${Math.floor(interval)} months ago`;
      }
    }

    interval = seconds / 86400; // Number of seconds in a day
    if (interval === 1) {
      return `Last run 1 day ago`;
    } else if (interval > 1) {
      return `Last run ${Math.floor(interval)} days ago`;
    }

    interval = seconds / 3600; // Number of seconds in an hour
    if (interval === 1) {
      return `Last run 1 hour ago`;
    } else if (interval > 1) {
      return `Last run ${Math.floor(interval)} hours ago`;
    }

    return 'Last run just now';
  }

  static getUserFullName(currentUser: { name: string } | null): string {
    if (currentUser && currentUser.name) {
      return currentUser.name;
    } else {
      return '';
    }
  }

  static getUserInitials(currentUser: { name: string } | null): string {
    if (currentUser && currentUser.name) {
      const fullName = currentUser.name;
      const parts = fullName.split(' ');
      const firstLetterFirstPart = parts[0]?.charAt(0) || '';
      const firstLetterLastPart = parts[parts.length - 1]?.charAt(0) || '';
      return firstLetterFirstPart + firstLetterLastPart;
    } else {
      return '';
    }
  }

  static removeHttpsFromUrl(url: string) {
    return url.replace(/^https?:\/\//, '');
  }

  static isRegressionModel(configs: any): boolean {
    if (!configs) {
      return false;
    }
    if ('problem_type' in configs) {
      return configs.problem_type === ProblemType.Regression;
    }
    return false;
  }

  static isClassificationModel(configs: any): boolean {
    if (!configs) {
      return false;
    }
    if ('problem_type' in configs) {
      return configs.problem_type === ProblemType.Classification;
    }
    return false;
  }

  static convertDataToIncludeBooleanFlagsForCheckboxFuctionality(listOfAllElements: any, listOfSelectedElements: any) {
      let selectedColumnsList:any;
      if(listOfSelectedElements.length > 0) {
        selectedColumnsList = listOfSelectedElements.map((name: any) => ({ 
          name: name, 
          checked: false 
        }));
      }
      else {
        selectedColumnsList = []
      }
  
      const selectedSet = new Set(listOfSelectedElements)
  
      let columnsList = listOfAllElements.filter((name: any) => !selectedSet.has(name)).map((name: string) => ({ 
        name: name, 
        checked: false 
      }));
  
      return {
        columnsList,
        selectedColumnsList
      }
    }
}
