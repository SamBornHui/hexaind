import { Component, Input, ElementRef, SimpleChanges, OnChanges, resolveForwardRef, OnDestroy } from '@angular/core';
import { DataPreviewService } from '../services/data-preview.service'
import { MatTableDataSource } from '@angular/material/table';
import { SelectionModel } from '@angular/cdk/collections';
import * as Plotly from 'plotly.js-dist-min';
import { Data, Layout, Annotations } from 'plotly.js-dist-min';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ConfigService } from '../../../services/config.service';
import { catchError, interval, of, Subscription, switchMap, takeWhile } from 'rxjs';

export interface Statistic {
  "Column Name": string;
  min: number;
  max: number;
  mean: number;
  isFlagged?: boolean;
}

interface GraphConfig {
  id: string;
  xAxis: string;
  yAxis: string;
  type: string;
  interactive: boolean;
  colourBy: string;
}

interface GraphData {
  [key: string]: SafeResourceUrl | undefined;
}

interface LoadingState {
  [key: string]: boolean;
}

interface TableRow {
  first_column: any;
  [key: string]: any;
}

@Component({
  selector: 'app-correlation',
  templateUrl: './correlation.component.html',
  styleUrls: ['./correlation.component.less']
})
export class CorrelationComponent implements OnChanges, OnDestroy {
  @Input() dataset_id!: string;

  selection = new SelectionModel<Statistic>(true, []);
  dataSource!: MatTableDataSource<Statistic>;
  numericalDataSource: TableRow[] = [];
  correlationDataSource!: MatTableDataSource<TableRow>;
  numericalColumns: string[] = [];
  sortedNumericalColumns: string[] = [];
  xAxisColumnNames: string[] = [];
  yAxisColumnNames: string[] = [];
  selectedXAxisColumnName: string = ""
  selectedYAxisColumnName: string = ""
  selectedColourBy: string = ""
  displayedColumns: string[] = ['select', 'Column Name', 'flagged', 'min', 'max', 'mean']
  filteredData: any[] = [];
  flaggedState: boolean[] = [];
  cellHeights: any
  isPlotsGenerated: boolean = false
  _interactive: boolean = false
  plotData: Map<string, SafeResourceUrl>;
  // isLoading: Record<string, boolean>;
  data: any
  heatmapData: any
  excludedColumns: string[] = ['Pareto-optimal_num', 'generation_method', 'trial_index', 'visual_dir', 'arm_name'];
  isLoading: { [key: string]: boolean } = { graph1: false, graph2: false, graph3: false };
  showLoader: boolean = false;
  isScientificNotationEnabled: boolean = false;
  heatMap: any;


  private annotations: Partial<Plotly.Annotations>[] = [];

  // Parameters for correlation plot
  minPeriod: number | undefined;
  clipPercentiles: number = 99.5;
  symmetricBounds: boolean = true;

  loadingHeatmap: boolean = false;
  isCorrelationError: boolean = false;

  correlationHeatmapSubscription: Subscription | null = null;
  visualizationSubscription: Subscription | null = null;

  POLLING_INTERVAL = 5000;

  additional_config: any;

  isNoNumericalColumns: boolean = false;
  numericalDisplayedColumns: string[] = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'missing'];
  private categoricalColumnNames: string[] = []

  constructor(private dataPreviewService: DataPreviewService, private elementRef: ElementRef, private sanitizer: DomSanitizer, private configService: ConfigService) {
    this.plotData = new Map();
    this.isLoading = { graph1: false, graph2: false, graph3: false };
    this.annotations = [];
  }

  ngOnInit() {
  }

  ngOnDestroy() {
    this.correlationHeatmapSubscription?.unsubscribe();
    this.visualizationSubscription?.unsubscribe();
    this.dataPreviewService.unsubscribeNumerical();
    this.dataPreviewService.unsubscribeCategorical();
  }

  async setDataSource() {
    this.isNoNumericalColumns = false;
    const numerical = await this.dataPreviewService.loadNumericalData(this.dataset_id)
    if (numerical) {
      this.prepareNumericalTableData(numerical.statistics[0]);
      this.numericalColumns = numerical.statistics[0].column_names;
    }
    this.dataPreviewService.unsubscribeNumerical();

    this.dataPreviewService.getNumericalDataSourceObservable().subscribe((data: any) => {
      this.dataSource = new MatTableDataSource<Statistic>(data);
      this.dataSource.data.forEach(row => row.isFlagged = false);
      this.dataSource.data = this.dataSource.data.filter((el: any) => !this.excludedColumns.includes(el['Column Name']))
      if (this.dataSource.filteredData.length === 0) this.isNoNumericalColumns = true;
    });

    this.dataPreviewService.getCategoricalColumnNamesObservable().subscribe((data: any) => {
      this.categoricalColumnNames = data;
    });

    // this.dataPreviewService.getNumericalColumnNamesObservable().subscribe((columnNames: any) => {
    //   this.numericalColumns = columnNames
    // });
  }

  prepareNumericalTableData(data: any) {
    const columnNames = ['Column Name'].concat(this.numericalDisplayedColumns);
    const rows = data.data;
    const firstColumn = data.column_names;

    this.numericalDataSource = rows.map((row: any[], index: string | number) => {
      const rowData: { [key: string]: any } = { 'Column Name': firstColumn[index] };
      row.forEach((cell: any, idx: number) => {
        rowData[columnNames[idx + 1]] = cell;
      });
      return rowData;
    });
    this.dataPreviewService.updateNumericalDataSource(this.numericalDataSource);
    this.numericalDisplayedColumns = columnNames;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataset_id']) {
      const previousValue = changes['dataset_id'].previousValue;
      const currentValue = changes['dataset_id'].currentValue;

      if (previousValue !== currentValue) {
        this.setDataSource();
      }
    }
  }

  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }

  masterToggle() {
    if (this.isAllSelected()) {
      this.selection.clear();
    } else {
      this.dataSource.data.forEach(row => this.selection.select(row));
    }
  }

  onFlagClick(element: Statistic) {
    element.isFlagged = !element.isFlagged;
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  backToColumnsScreen() {
    this.isPlotsGenerated = !this.isPlotsGenerated;
  }

  async generatePlots() {
    this.showHeatmapLoadingSpinner();
    this.isCorrelationError = false;
    if (this.selection.selected.length >= 2) {
      this.isPlotsGenerated = !this.isPlotsGenerated;
      this.numericalColumns = this.dataSource.filteredData
        .filter(row => this.selection.selected.some(selected => selected['Column Name'] === row['Column Name']))
        .map(row => row['Column Name']);
      this.sortedNumericalColumns = this.numericalColumns;
      // this.sortedNumericalColumns.sort();
      this.xAxisColumnNames = this.numericalColumns
      const reverseArray: string[] = [];
      this.xAxisColumnNames.map((value) => {
        reverseArray.unshift(value);
      });
      this.yAxisColumnNames = reverseArray;
      this.selectedXAxisColumnName = this.xAxisColumnNames[0]
      this.selectedYAxisColumnName = this.yAxisColumnNames[0]

      this.additional_config = {
        "min_period": this.minPeriod !== undefined ? this.minPeriod : null,
        "clip_percentiles": this.clipPercentiles,
        "symmetric_bounds": this.symmetricBounds
      }



      this.dataPreviewService.getCorrelationHeatmap(this.dataset_id, this.sortedNumericalColumns, this.additional_config).then(response => {
        if (response) {
          if (response.data?.file_path) {
            this.setHeatmapData(response);
          } else {
            this.pollForCorrelationHeatmap();
          }
        }
      }).catch(error => {
        console.error('Error:', error);
        this.isCorrelationError = true;
        this.stopHeatmapLoadingSpinner();
      });
    }
  }

  setHeatmapData(response: any) {
    this.heatMap = this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${response.data.file_path}`);
    this.stopHeatmapLoadingSpinner();
    this.preparePlotsPayloadAndFetchData();
  }

  pollForCorrelationHeatmap() {
    this.correlationHeatmapSubscription = interval(this.POLLING_INTERVAL)
      .pipe(
        switchMap(() => this.dataPreviewService.getCorrelationHeatmap(this.dataset_id, this.sortedNumericalColumns, this.additional_config)),
        takeWhile(response => !response?.data?.file_path, true),
        catchError(error => {
          console.error('Error during polling:', error);
          this.correlationHeatmapSubscription?.unsubscribe();
          return of(null);
        })
      )
      .subscribe(response => {
        if (response && response.data?.file_path) {
          this.setHeatmapData(response);
          this.correlationHeatmapSubscription?.unsubscribe();
        }
      });
  }

  onXAxisChange(value: string) {
    this.preparePlotsPayloadAndFetchData();
  }

  onYAxisChange(value: string) {
    this.preparePlotsPayloadAndFetchData();
  }

  onColourByChange(value: string) {
    this.preparePlotsPayloadAndFetchData();
  }

  async preparePlotsPayloadAndFetchData() {
    this.showLoader = true;

    let graphConfigs;
    if (this.selectedXAxisColumnName === this.selectedYAxisColumnName) {
      graphConfigs = [
        { id: 'graph1', xAxis: this.selectedXAxisColumnName, yAxis: this.selectedXAxisColumnName, type: 'DISTRIBUTION', interactive: this.interactive, colourBy: this.selectedColourBy },
      ];
    } else {
      graphConfigs = [
        { id: 'graph1', xAxis: this.selectedXAxisColumnName, yAxis: this.selectedYAxisColumnName, type: 'DISTRIBUTION', interactive: this.interactive, colourBy: this.selectedColourBy },
        // { id: 'graph2', xAxis: this.selectedXAxisColumnName, yAxis: this.selectedXAxisColumnName, type: 'DISTRIBUTION', interactive: this.interactive, colourBy: this.selectedColourBy },
        // { id: 'graph3', xAxis: this.selectedYAxisColumnName, yAxis: this.selectedYAxisColumnName, type: 'DISTRIBUTION', interactive: this.interactive, colourBy: this.selectedColourBy },
      ];
    }

    try {
      await Promise.all(graphConfigs.map(async (config) => {
        const data = await this.fetchPlotData(config);
        if (graphConfigs.length === 1) {
          this.plotData.set(config.id, data);
          // this.plotData.set('graph2', '');
          // this.plotData.set('graph3', '');
        } else {
          this.plotData.set(config.id, data);
        }
      }));
    } catch (error) {
      console.error(`Error fetching data:`, error);
    } finally {
      this.showLoader = false;
    }
  }

  pollForVisualization(config: GraphConfig, resolve: (url: SafeResourceUrl) => void, reject: (error: any) => void) {
    this.visualizationSubscription = interval(this.POLLING_INTERVAL)
      .pipe(
        switchMap(() => this.dataPreviewService.getVisualization(
          this.dataset_id,
          config.xAxis,
          config.yAxis,
          config.type,
          config.interactive,
          config.colourBy
        )),
        takeWhile(response => !response, true),
        catchError(error => {
          console.error('Error during polling:', error);
          reject(new Error('Error during polling'));
          this.visualizationSubscription?.unsubscribe();
          return of(null);
        })
      )
      .subscribe(response => {
        if (response) {
          const safeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
            `${this.configService.getAppAuxApiURL}/eda/file?path=${response}`
          );
          this.visualizationSubscription?.unsubscribe();
          resolve(safeUrl);
        }
      });
  }

  async fetchPlotData(config: GraphConfig): Promise<SafeResourceUrl> {
    try {
      const response = await this.dataPreviewService.getVisualization(
        this.dataset_id,
        config.xAxis,
        config.yAxis,
        config.type,
        config.interactive,
        config.colourBy
      );

      if (response) {
        return this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${response}`);
      } else {
        return new Promise<SafeResourceUrl>((resolve, reject) => {
          this.pollForVisualization(config, resolve, reject);
        });
      }
    } catch (error) {
      throw new Error('Error fetching graph data');
    }
  }

  get availableColourByOptions(): string[] {
    return this.xAxisColumnNames.concat(this.categoricalColumnNames).filter(name =>
      name !== this.selectedXAxisColumnName &&
      name !== this.selectedYAxisColumnName
    );
  }

  getIconUrl(index: number): string {
    return this.flaggedState[index]
      ? 'flag'
      : 'outlined_flag';
  }

  async initializeHeatmap() {
    if (!this.heatmapData?.corr_heatmap) {
      return;
    }

    const { vmin, vmax } = this.calculatePercentiles(this.heatmapData.corr_heatmap.heatmap_data_z, this.clipPercentiles);

    const colorscale: any[] = [
      [0.0, 'rgb(127, 59, 8)'],      // First color
      [0.1, 'rgb(179, 88, 6)'],       // Second color
      [0.2, 'rgb(224, 130, 20)'],     // Third color
      [0.3, 'rgb(253, 184, 99)'],     // Fourth color
      [0.4, 'rgb(254, 224, 182)'],    // Fifth color
      [0.5, 'rgb(247, 247, 247)'],    // Midpoint color (white)
      [0.6, 'rgb(216, 218, 235)'],     // Sixth color
      [0.7, 'rgb(178, 171, 210)'],     // Seventh color
      [0.8, 'rgb(128, 115, 172)'],     // Eighth color
      [0.9, 'rgb(84, 39, 136)'],       // Ninth color
      [1.0, 'rgb(45, 0, 75)']          // Last color
    ];

    const truncatedLabelsX = this.heatmapData.corr_heatmap.heatmap_data_x.map((label: string) =>
      label.length > 20 ? `${label.slice(0, 20)}...` : label
    );
    const truncatedLabelsY = this.heatmapData.corr_heatmap.heatmap_data_y.map((label: string) =>
      label.length > 20 ? `${label.slice(0, 20)}...` : label
    )

    const zData = this.heatmapData.corr_heatmap.heatmap_data_z.map((row: number[], i: number) =>
      row.map((val: number, j: number) => (i > j ? val : null))
    );

    const hoverText = zData.map((row: number[], i: number) =>
      row.map((val: number, j: number) =>
        `X: ${this.heatmapData.corr_heatmap.heatmap_data_x[j]}<br>
         Y: ${this.heatmapData.corr_heatmap.heatmap_data_y[i]}<br>
         Z: ${val}`
      )
    );

    const data: Data[] = [{
      x: truncatedLabelsX,
      y: truncatedLabelsY,
      z: zData,
      hovertext: hoverText,
      hoverinfo: 'text',
      colorscale: colorscale,
      type: 'heatmap',
      zmin: this.heatmapData.corr_heatmap.vmin,
      zmax: this.heatmapData.corr_heatmap.vmax,
    }];

    this.data = data
    this.annotations = this.createAnnotations(this.data);



    // Define the layout for the plot
    let layout: Partial<Layout> = {
      autosize: true,
      xaxis: {
        showgrid: false,
        automargin: true
      },
      yaxis: {
        showgrid: false,
        autorange: 'reversed',  // Ensures the diagonal goes top-left to bottom-right
        tickangle: 0,           // No rotation for y-axis labels
        automargin: true
      },
      plot_bgcolor: 'white',
      margin: {
        l: 10,
        r: 10,
        t: 10
      }
    };

    Plotly.newPlot('heatmap', data, layout).then((plot: any) => {
      plot.on('plotly_click', (eventData: any) => this.onSelect(eventData));
    }).then(
      () => {
        this.drawInitialBorder();
        this.preparePlotsPayloadAndFetchData();
        this.stopHeatmapLoadingSpinner()
      }
    );


    const numRows = this.heatmapData.corr_heatmap.heatmap_data_z.length;
    const heatmapContainer = this.elementRef.nativeElement.getElementsByClassName('nsewdrag ')[0];
    const heightOfSVG = heatmapContainer.getClientRects()[0].height
    this.cellHeights = heightOfSVG / numRows;
  }

  showHeatmapLoadingSpinner() {
    this.loadingHeatmap = true;
    // const heatmapDiv = document.getElementById('heatmap');
    // if (heatmapDiv) heatmapDiv.style.display = 'none';
  }

  stopHeatmapLoadingSpinner() {
    this.loadingHeatmap = false;
    this.correlationHeatmapSubscription?.unsubscribe();
    // const heatmapDiv = document.getElementById('heatmap');
    // if (heatmapDiv && !this.isCorrelationError) heatmapDiv.style.display = 'block';
  }

  calculatePercentiles(corrMatrix: number[][], clipPercentile: number): { vmin: number, vmax: number } {
    // Flatten the 2D array and filter out NaN values
    const flattened = corrMatrix.flat().filter(value => !isNaN(value));

    // Sort the flattened array
    flattened.sort((a, b) => a - b);

    // Calculate the index for the percentiles
    const lowerIndex = Math.floor((clipPercentile / 100) * flattened.length);
    const upperIndex = Math.floor(((100 - clipPercentile) / 100) * flattened.length);

    // Get the min and max values based on the indices
    const vmin = flattened[lowerIndex];
    const vmax = flattened[upperIndex];

    return { vmin, vmax };
  }


  createAnnotations(data: any): Partial<Plotly.Annotations>[] {
    let annotations: any[] = [];
    for (let i = 0; i < data[0].z.length; i++) {
      for (let j = 0; j < data[0].z[i].length; j++) {
        let result = {
          x: data[0].x[j],
          y: data[0].y[i],
          text: (data[0].z[i][j]) ? data[0].z[i][j].toString() : "",
          xref: 'x',
          yref: 'y',
          showarrow: false,
          font: {
            family: 'Arial',
            size: 12,
            color: 'white'
          }
        }
        annotations.push(result);

      }
    }
    return annotations;
  }

  onSelect(eventData: any) {
    if (eventData.points && eventData.points.length > 0) {
      const point = eventData.points[0];

      const xIndex = this.data[0].x.indexOf(point.x);
      const yIndex = this.data[0].y.indexOf(point.y);

      if (xIndex !== -1 && yIndex !== -1) {
        const x0 = xIndex - 0.5;
        const x1 = xIndex + 0.5;
        const y0 = yIndex - 0.5;
        const y1 = yIndex + 0.5;

        this.drawBorder(x0, y0, x1, y1);
      }

      this.selectedXAxisColumnName = this.heatmapData.corr_heatmap.heatmap_data_x[xIndex];
      this.selectedYAxisColumnName = this.heatmapData.corr_heatmap.heatmap_data_y[yIndex];
      this.preparePlotsPayloadAndFetchData()
    }
  }

  drawInitialBorder() {
    const xIndex = this.data[0].x.indexOf(this.selectedXAxisColumnName);
    const yIndex = this.data[0].y.indexOf(this.selectedYAxisColumnName);

    if (xIndex !== -1 && yIndex !== -1) {
      // Calculate cell boundaries based on the indices
      const x0 = xIndex - 0.5;
      const x1 = xIndex + 0.5;
      const y0 = yIndex - 0.5;
      const y1 = yIndex + 0.5;

      this.drawBorder(x0, y0, x1, y1);
    }
  }

  drawBorder(x0: number, y0: number, x1: number, y1: number) {
    const borderShape: any = {
      type: 'rect',
      xref: 'x',
      yref: 'y',
      x0: x0,
      y0: y0,
      x1: x1,
      y1: y1,
      line: {
        color: 'red',
        width: 3,
      },
      fillcolor: 'rgba(0,0,0,0)'
    };

    Plotly.relayout('heatmap', { shapes: [borderShape] });
  }

  get interactive(): boolean {
    return this._interactive;
  }

  set interactive(value: boolean) {
    this._interactive = value;
    this.preparePlotsPayloadAndFetchData()
  }
}
