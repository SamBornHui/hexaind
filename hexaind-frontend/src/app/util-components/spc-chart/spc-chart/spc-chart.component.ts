import { Component, ViewChild, AfterViewInit, Input } from '@angular/core';
import { ChartOptions, ChartDataset, Chart } from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import { BaseChartDirective } from 'ng2-charts';
import 'chartjs-adapter-date-fns';
import { ApiService } from 'src/app/services/api.service';

Chart.register(annotationPlugin);
@Component({
  selector: 'app-spc-chart',
  templateUrl: './spc-chart.component.html',
  styleUrls: ['./spc-chart.component.less']
})
export class SpcChartComponent {
  @ViewChild(BaseChartDirective) chart!: BaseChartDirective;
  @Input() selectedChamberId: any;
  @Input() chamberIdLength: any;
  @Input() currentProjectName: any;
  @Input() currentWorkWeekFolderName: any;
  @Input() currentSelectedOutputColumn: any;

  // public chamberIdLength: any;
  public beforeMeanValue: any;
  public afterMeanValue: any;
  public beforeStdValue: any;
  public afterStdValue: any;
  public uclInputValue: any;
  public lclInputValue: any;
  public uclDateRangeValue: any;
  public lclDateRangeValue: any;
  public targetInputValue: any ;
  public before_cpk: any ;
  public after_cpk: any;
  public meanInside: any;
  public meanOutside: any;
  public stdDevInside: any;
  public stdDevOutside: any;
  public cpkInside: any;
  public cpkOutside: any;

  public movableX : any;
  public startRange: any;
  public endRange : any;
  public minDate: Date = new Date();
  public maxDate :Date = new Date();
  public startRangeString: any;
  public endRangeString: any;
  public movableXTimestamp: any = new Date(); // Convert to timestamp
  public responseData : any = {};
  public colorIndex= 0;
  public showLoader = true;
  public displayedColumns = ['chamber_id', 'Mean','stdDev', 'CPK']
  public Chamber_Table : any = [];
  public dataSource :  any;
  public chamberGroups = new Map<string, any[]>();
  public originalData: {
   x: Date; y: any;chamber_id: any
}[] = [];
  public isButtonParameter: boolean = false;
  public isButtonRangeParameter: boolean = false;

  public chartData: ChartDataset<'scatter'>[] = [];
  public chartOptions: ChartOptions<'scatter'> = {
    responsive: true,
    plugins: {
      
      legend: { display: true },
      annotation: {
        annotations: {
          movableLine: {
            type: 'line',
            borderColor: 'black',
            borderWidth: 2,
            borderDash: [5, 5],
            label: { display: true, position: 'top' }
          } as any
        }
      },
      tooltip: {
        callbacks: {
          label: (tooltipItem) => {
            const dataPoint = tooltipItem.raw as any; // Get the hovered data point
            const date = new Date(dataPoint.x).toLocaleDateString('en-US', {  
              year: 'numeric', month: 'short', day: 'numeric'  
            }); // Format date as "MMM dd, yyyy"
            return [
              `Chamber id: ${dataPoint.chamber_id}`,
              `Value: ${dataPoint.y.toFixed(2)}`,
              `Date: ${date}`
            ];;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time',  // Set time scale
        time: {
          unit: 'day',  // Set time unit (change to 'month', 'hour', etc., if needed)
          tooltipFormat: 'MMM dd, yyyy', // Tooltip date format
          displayFormats: {
            day: 'MMM dd', //  X-axis labels format
            hour: 'HH:mm',
          }
        },
        ticks: {
          source: 'data', // Use data points for positioning
          autoSkip: true,  // Prevents labels from overlapping
          maxRotation: 0,  // Keeps the labels horizontal
          minRotation: 0,
          maxTicksLimit: 10
        },
        title: { display: true, text: 'Date' },
        // grid: { display: false }
      },
      
      y: { 
        title: { display: true, text: 'output_values' },
        ticks: {
          // precision: 2, // Ensures 2 decimal places
          // locale: 'en-US'
          }
        // grid: { display: false }
        
      }
    }
  };

  public chartDataRange: ChartDataset<'scatter'>[] = [];
  public chartRangeOptions: ChartOptions<'scatter'> = {
    responsive: true,
    plugins: {
      legend: { display: true },
      tooltip: {
        callbacks: {
          label: (tooltipItem) => {
            const dataPoint = tooltipItem.raw as any; // Get the hovered data point
            const date = new Date(dataPoint.x).toLocaleDateString('en-US', {  
              year: 'numeric', month: 'short', day: 'numeric'  
            }); // Format date as "MMM dd, yyyy"
            return [
              `Chamber id: ${dataPoint.chamber_id}`,
              `Value: ${dataPoint.y.toFixed(2)}`,
              `Date: ${date}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time',  //  Set X-axis as time scale
        time: {
          unit: 'day',
          tooltipFormat: 'MMM dd, yyyy',
          displayFormats: { day: 'MMM dd' }
        },
        ticks: {
          source: 'data', // Use data points for positioning
          autoSkip: true,  // Prevents labels from overlapping
          maxRotation: 0,  // Keeps the labels horizontal
          minRotation: 0,
          maxTicksLimit: 10 
        },
        title: { display: true, text: 'Date' }
      },
      y: { title: { display: true, text: 'output_values' } }
    }
  };

  isCPKButton: boolean = true;
  isMultiCPkButton: boolean = true;
  isDateComputeButton: boolean = true;

  constructor(
    private apiService: ApiService
  ) {
  }
  
  ngAfterViewInit() {
    // this.transformData(this.responseData);
    // this.setMovelineDate(this.responseData);
    // this.updateChartData();
    // this.updateChart();
    
  }

  ngOnInit(){
    this.fetchDataPoints(); 
    this.chamberIdLength = this.selectedChamberId.length;
    setTimeout(()=>{
      if(this.chamberIdLength == 1){
        this.updateChartData()
      }
    },1000)
  }

  async fetchDataPoints(){
    try {
      this.responseData = await this.apiService.getUC2SpcDataPoints(
        this.currentProjectName,
        this.currentWorkWeekFolderName,
        this.currentSelectedOutputColumn,
        this.selectedChamberId,
        false,
      );
      this.transformData(this.responseData);
    }
    catch{
      console.log("Api Error ");
    }

  }



  transformData(responseData: any): void {
    if (!responseData || !responseData.chambers) {
      return;
    }
    this.originalData = [];
    this.uclInputValue = responseData.ucl;
    this.lclInputValue = responseData.lcl;
    this.uclDateRangeValue = this.responseData.ucl;
    this.lclDateRangeValue = this.responseData.lcl;
    this.targetInputValue = responseData.target;
    for (const chamKey in responseData.chambers) {
      const chamber = responseData.chambers[chamKey];
      if (chamber.runcomplete_datetime && chamber.output_values) {
        const length = Math.min(chamber.runcomplete_datetime.length, chamber.output_values.length);
  
        for (let i = 0; i < length; i++) {
          this.originalData.push({
            x: new Date(chamber.runcomplete_datetime[i]), 
            y: chamber.output_values[i],
            chamber_id: chamKey
          });
        }
      }
    }
    if(this.chamberIdLength == 1){
      this.setMovelineDate(this.responseData);
    } else{
      this.filterRangeDataPoints(this.responseData);
    }
    
  }

  setMovelineDate(responseData: any): void {
    let allDates: Date[] = [];
    if (!responseData || !responseData.chambers) {
      return;
    }
  
    for (const chamKey in responseData.chambers) {
      const chamber = responseData.chambers[chamKey];
  
      if (chamber.runcomplete_datetime) {
        allDates.push(...chamber.runcomplete_datetime.map((dateStr: string) => new Date(dateStr)));
      }
    }
  
    if (allDates.length > 0) {
      allDates.sort((a, b) => a.getTime() - b.getTime()); // Sort dates in ascending order
  
      this.minDate = allDates[0];
      this.maxDate = allDates[allDates.length - 1];
  
      const midIndex = Math.floor(allDates.length / 2);
      this.movableX = allDates[midIndex];
    } 
    else{
      this.minDate = new Date();
      this.maxDate = new Date();
      this.movableX = new Date();
    }
    this.movableXTimestamp = this.movableX.getTime();  
    // this.movableX = new Date(this.movableXTimestamp);
    this.updateChartData();
  }

  updateChartData() {
    // const beforeLine = this.originalData.filter(point => point.x <= this.movableX);
    // const afterLine = this.originalData.filter(point => point.x > this.movableX);
    const beforeLine = this.originalData
      .filter(point => point.x <= this.movableX)
      .map(p => ({ x: p.x.getTime(), y: p.y, chamber_id: p.chamber_id })); // Include chamber_id

    const afterLine = this.originalData
      .filter(point => point.x > this.movableX)
      .map(p => ({ x: p.x.getTime(), y: p.y, chamber_id: p.chamber_id }));
    const beforeStats = this.calculateStats(beforeLine.map(p => p.y));
    const afterStats = this.calculateStats(afterLine.map(p => p.y));

    this.beforeMeanValue = beforeStats.mean.toFixed(2);
    this.afterMeanValue = afterStats.mean.toFixed(2);
    this.beforeStdValue = beforeStats.stdDev.toFixed(2);
    this.afterStdValue = afterStats.stdDev.toFixed(2);

    this.computeCPK();
    

    this.chartData = [
      { label: 'Before Line', data: beforeLine, backgroundColor: 'red', showLine: false, pointRadius: 4 },
      { label: 'After Line', data: afterLine, backgroundColor: 'blue', showLine: false, pointRadius: 4 }
    ];
    this.showLoader = false;
    this.updateChart();
  }

  moveLine(value: Event) {
    const inputElement = value.target as HTMLInputElement;  // Cast to HTMLInputElement
    this.movableXTimestamp = Number(inputElement.value); 
    this.movableX = new Date(this.movableXTimestamp);
    this.updateChartData();
  }

  filterRangeDataPoints(responseData: any): void {
    let allDates: Date[] = [];
    if (!responseData || !responseData.chambers) {
      return;
    }
  
    for (const chamKey in responseData.chambers) {
      const chamber = responseData.chambers[chamKey];
  
      if (chamber.runcomplete_datetime) {
        allDates.push(...chamber.runcomplete_datetime.map((dateStr: string) => new Date(dateStr)));
      }
    }
  
    if (allDates.length > 0) {
      allDates.sort((a, b) => a.getTime() - b.getTime()); // Sort dates in ascending order
  
      this.minDate = allDates[0];
      this.maxDate = allDates[allDates.length - 1];
  
      const midIndex = Math.floor(allDates.length / 2);
      const startIndex = Math.floor(allDates.length / 3);
      const endIndex = Math.floor((allDates.length * 2) / 3);
  
      this.startRange = allDates[startIndex];
      this.endRange = allDates[endIndex];
      
    } 
    else{
      this.startRange = new Date();
      this.endRange = new Date();
    }
    this.startRangeString = this.formatDate(this.startRange);
    this.endRangeString  = this.formatDate(this.endRange);
    this.filterDataByRange();
  }

  filterDataByRange() {
    // const insideRange = this.originalData.filter(point => point.x >= this.startRange && point.x <= this.endRange)
    // .map(p => ({ x: p.x.getTime(), y: p.y, chamber_id: p.chamber_id }));
    // const outsideRange = this.originalData.filter(point => point.x < this.startRange || point.x > this.endRange)
    // .map(p => ({ x: p.x.getTime(), y: p.y, chamber_id: p.chamber_id }));
    // const insideStats = this.calculateStats(insideRange.map(p => p.y));
    // const outsideStats = this.calculateStats(outsideRange.map(p => p.y));
    
    // this.meanInside = insideStats.mean.toFixed(2);
    // this.stdDevInside = insideStats.stdDev.toFixed(2);
    // this.meanOutside = outsideStats.mean.toFixed(2);
    // this.stdDevOutside = outsideStats.stdDev.toFixed(2)

    // this.computeMultiChamberCPK();
    this.chamberGroups = new Map<string, any[]>();
    this.originalData.forEach(point => {
      if (!this.chamberGroups.has(point.chamber_id)) {
        this.chamberGroups.set(point.chamber_id, []);
      }
      this.chamberGroups.get(point.chamber_id)?.push(point);
    });


    this.tableChartData();
    
    const insideChartRange = Array.from(this.chamberGroups.entries()).map(([chamber_id, points]) => ({
      label: chamber_id,
      data: points
        .filter(p => p.x >= this.startRange && p.x <= this.endRange) // Include inside range
        .map(p => ({ x :(p.x instanceof Date ? p.x.getTime() : p.x), y: p.y,chamber_id: chamber_id })),
      pointBackgroundColor: this.generateColor(chamber_id),
      pointRadius: 4, // Set size of points
      showLine: false
    }));


    const outsideChartRange = [{
      label: 'Outside Range',
      data: Array.from(this.chamberGroups.entries()).flatMap(([chamber_id, points]) =>
        points.filter(p => p.x < this.startRange || p.x > this.endRange)
          .map(p => ({ 
            x: (p.x instanceof Date ? p.x.getTime() : p.x), 
            y: p.y, 
            chamber_id: chamber_id 
          }))
      ),
      pointBackgroundColor: 'grey',
      pointRadius: 4,
      showLine: false
    }];

    
    console.log("outsideChartRange : ",insideChartRange);
    // this.chartDataRange = [
    //   { label: 'Outside Range', data: outsideChartRange.data, pointBackgroundColor: 'grey', showLine: false, pointRadius: 4 },
    //   ...insideChartRange
    // ];
    this.chartDataRange = [
      ...outsideChartRange, // Outside Range Data
      ...insideChartRange   // Inside Range Data
    ];
    this.showLoader = false;
    
    this.updateChart();
  }

  updateChart() {
    if (this.chart) {
      (this.chart.options!.plugins!.annotation as any).annotations.movableLine.xMin = this.movableX.getTime();
      (this.chart.options!.plugins!.annotation as any).annotations.movableLine.xMax = this.movableX.getTime();
      this.chart.update();
    }
  }

  tableChartData(){
    if(this.chamberGroups.entries()){
      this.Chamber_Table = Array.from(this.chamberGroups.entries()).map(([chamber_id, points]) =>{
        this.meanInside = this.calculateMean(points, true);
        this.meanOutside = this.calculateMean(points, false);
        this.stdDevInside = this.calculatestdDev(points,true);
        this.stdDevOutside = this.calculatestdDev(points,false)
      
        return {
          chamber_id: chamber_id,
          mean_insideRange: this.meanInside,
          mean_outsideRange: this.meanOutside,
          stdDev_insideRange : this.stdDevInside,
          stdDev_outsideRange : this.stdDevOutside,
          CPK_insideRange : this.calculateCPK(points,true,this.meanInside,this.meanOutside,this.stdDevInside,this.stdDevOutside),
          CPK_outsideRange : this.calculateCPK(points,false,this.meanInside,this.meanOutside,this.stdDevInside,this.stdDevOutside)
        };
  
      })

      this.isMultiCPkButton = true;
    }
  }


  calculateMean(points: any[], isStartRange: boolean){
    let filteredPoints;
    if(isStartRange){
      filteredPoints = points.filter(point => point.x >= this.startRange && point.x <= this.endRange)
    .map(p => p.y );
    }
    else{
      filteredPoints = points.filter(point => point.x < this.startRange || point.x > this.endRange)
    .map(p => p.y)
    }
    
    if (filteredPoints.length === 0) return;
    return (this.calculateStats(filteredPoints).mean).toFixed(2);
  }

  calculatestdDev(points: any[], isStartRange: boolean){
    let filteredPoints;
    if(isStartRange){
      filteredPoints = points.filter(point => point.x >= this.startRange && point.x <= this.endRange)
    .map(p => p.y );
    }
    else{
      filteredPoints = points.filter(point => point.x < this.startRange || point.x > this.endRange)
    .map(p => p.y)
    }
    
    if (filteredPoints.length === 0) return; // Handle empty case
    return (this.calculateStats(filteredPoints).stdDev).toFixed(2);
  }

  calculateCPK(points: any[], isStartRange: boolean,mean_insideRange : any,mean_outsideRange : any,stdDev_insideRange : any,stdDev_outsideRange : any){
    if(isStartRange){
      const beforeCPK = Math.min(
        (this.uclDateRangeValue - mean_insideRange) / (3 * stdDev_insideRange),
        (mean_insideRange - this.lclDateRangeValue) / (3 * stdDev_insideRange)
      );
      // this.before_cpk = beforeCPK.toFixed(2);
      return beforeCPK.toFixed(2)
    }
    else{
      const afterCPK = Math.min(
        (this.uclDateRangeValue - mean_outsideRange) / (3 * stdDev_outsideRange),
        (mean_outsideRange - this.lclDateRangeValue) / (3 * stdDev_outsideRange)
      );
      // this.after_cpk = afterCPK.toFixed(2);
      return afterCPK.toFixed(2)
    }
    
    // if (filteredPoints.length === 0) return; // Handle empty case
    // return (this.calculateStats(filteredPoints).stdDev).toFixed(2);
  }


  calculateStats(data: number[]): { mean: number; stdDev: number } {
    if (data.length === 0) return { mean: 0, stdDev: 0 };
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
    return { mean, stdDev: Math.sqrt(variance) };
  }

  computeCPK() {
    if (this.uclInputValue && this.lclInputValue) {
      const beforeCPK = Math.min(
        (this.uclInputValue - this.beforeMeanValue) / (3 * this.beforeStdValue),
        (this.beforeMeanValue - this.lclInputValue) / (3 * this.beforeStdValue)
      );
      const afterCPK = Math.min(
        (this.uclInputValue - this.afterMeanValue) / (3 * this.afterStdValue),
        (this.afterMeanValue - this.lclInputValue) / (3 * this.afterStdValue)
      );

      this.before_cpk = beforeCPK.toFixed(2);
      this.after_cpk = afterCPK.toFixed(2);
      this.isCPKButton = true;
    }
  }

  computeMultiChamberCPK() {
    if (this.uclDateRangeValue && this.lclDateRangeValue) {
      const beforeCPK = Math.min(
        (this.uclDateRangeValue - this.meanInside) / (3 * this.stdDevInside),
        (this.meanInside - this.lclDateRangeValue) / (3 * this.stdDevInside)
      );
      const afterCPK = Math.min(
        (this.uclDateRangeValue - this.meanOutside) / (3 * this.stdDevOutside),
        (this.meanOutside - this.lclDateRangeValue) / (3 * this.stdDevOutside)
      );

      this.cpkInside = beforeCPK.toFixed(2);
      this.cpkOutside = afterCPK.toFixed(2);
      this.isMultiCPkButton = true;
    }
  }

  validate(){
    this.isCPKButton = false;
  }

  validateMultiCPKButton(){
    this.isMultiCPkButton = false
  }

  formatDate(date: Date): string {
    return date.toISOString().split('T')[0]; // Extract YYYY-MM-DD
  }
  
  // Update startRange when the input field changes
  updateStartRange() {
    this.startRange = new Date(this.startRangeString);
    if(this.startRange < this.endRange){
      this.isDateComputeButton = false;
    }
    else{
      this.isDateComputeButton = true;
    }
  }

  updateEndRange() {
    this.endRange = new Date(this.endRangeString);
    if(this.startRange < this.endRange){
      this.isDateComputeButton = false
    }
    else{
      this.isDateComputeButton = true;
    }
  }
  generateColor(chamberId: string): string {
    const colors = ['red', 'blue', 'orange', 'green', 'purple', 'cyan', 'magenta', 'Tan', 'Maroon'];
    const assignedColor = colors[this.colorIndex]; // Pick the next color
    this.colorIndex = (this.colorIndex + 1) % colors.length; // Loop back after last color

    return assignedColor;
  }

  async computeFFParamater(){
    this.responseData =  await this.apiService.getUC2SpcDataPoints(
      this.currentProjectName,
      this.currentWorkWeekFolderName,
      this.currentSelectedOutputColumn,
      this.selectedChamberId,
      true,
    );
    this.isButtonParameter = true;
    this.isButtonRangeParameter = true;
    this.transformData(this.responseData);
  }

  async returnComputeFFParamater(){
    this.responseData =  await this.apiService.getUC2SpcDataPoints(
      this.currentProjectName,
      this.currentWorkWeekFolderName,
      this.currentSelectedOutputColumn,
      this.selectedChamberId,
      false,
    );
    this.isButtonParameter = false;
    this.isButtonRangeParameter = false;
    this.transformData(this.responseData);
  }

  reset(){
    this.uclInputValue = this.responseData.ucl;
    this.lclInputValue = this.responseData.lcl;
    this.targetInputValue = this.responseData.target;
    this.computeCPK();
  }

  resetDateRange(){
    this.uclDateRangeValue = this.responseData.ucl;
    this.lclDateRangeValue = this.responseData.lcl;
    this.targetInputValue = this.responseData.target;
    this.tableChartData();
  }

}
