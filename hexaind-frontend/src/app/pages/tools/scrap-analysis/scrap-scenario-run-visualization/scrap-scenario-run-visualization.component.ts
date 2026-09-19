import { 
  Component, 
  OnInit, 
  ViewChild, 
  Input, 
  Output, 
  EventEmitter, 
  HostListener,
  AfterViewInit, 
  QueryList,
  ViewChildren,
  ElementRef 
} from '@angular/core';
import {
  HttpClient,
  HttpEventType,
} from '@angular/common/http';
import { Subscription } from 'rxjs';
import * as Plotly from 'plotly.js-dist-min';
import { ToastrService } from 'ngx-toastr';
import { MatTableDataSource } from '@angular/material/table';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ScrapAnalysisService } from '../services/scrap-analysis.service'
import { DomSanitizer } from '@angular/platform-browser';
import { MatCheckboxChange } from '@angular/material/checkbox';


@Component({
  selector: 'app-scrap-run-vizualization',
  templateUrl: './scrap-scenario-run-visualization.component.html',
  styleUrls: ['./scrap-scenario-run-visualization.component.less'],
})
export class ScrapRunVizualizationComponent implements OnInit, AfterViewInit {
  @Input() usecaseDetail: any;
  @Input() scrapAllFiles: any;
  @Output() editScenarioEvent = new EventEmitter();
  @ViewChild('visualization0') public visualization0!: ElementRef;
  @ViewChild('visualization1') public visualization1!: ElementRef;
  constructor(
    private http: HttpClient,
    public toaster: ToastrService,
    private configService: ConfigService,
    private router: Router,
    private errorHandlerService: ErrorHandlerService,
    private scrapAnalysisService:ScrapAnalysisService,
    private sanitizer: DomSanitizer

  ) {
  }

  showMainHeader: boolean = false;
  scenarios: any[] = [];


  scrapColumns: string[] = [
    'Alloy',
    'Cost',
    'Source',
    'Available Weight',
    'Si',
    'Mg',
    'Cu',
    'Fe',
    'Mn',
    'Cr',
    'Zn',
    'Ti'
  ];

  demandColumns: string[] = [
    'Alloy',
    'Visualize',
    'Plant',
    'Supply',
    'Si',
    'Mg',
    'Cu',
    'Fe',
    'Mn',
    'Cr',
    'Zn',
    'Ti'
  ];

  limitColumns: string[] = [
    'Plant',
    'Scrap',
    'Demand'
  ];

  selectedDemand: string = '';
  baseLineSelect: boolean = true; 
  allDemands: any[] = [];
  plots: any[] = [];
  plotResults:any[] = [];
  loadingPlot: boolean = false;
  changeMade: boolean = false;

  ngOnInit(): void {
    this.scenarios = this.convertDbObjectToReadable(this.usecaseDetail);
    this.makeDemandSelection();
  }

  disableDownloadAll(){
    return (this.savedPlots().length>0)?false:true;
  }
  disableSave(){
    return this.loadingPlot;
  }
  disablePlot(){
    return (this.loadingPlot || !this.changeMade)?true:false;
  }

  drawVizualizationFromJSON(){
    Plotly.newPlot('visualization0', this.plotResults[0].data, this.plotResults[0].layout)
    Plotly.newPlot('visualization1', this.plotResults[1].data, this.plotResults[1].layout)  
  }
  onCheckboxChange(event: MatCheckboxChange, scenario: any) {
    this.changeMade = true;
  }
  
  checkPlotExists(plot:any,vizualizations:any){
    if(vizualizations.length==0){
      return false;
    }else{
      const visualizationExists = vizualizations.some((visualization:any) => 
        visualization.alloy === plot.alloy && 
        visualization.furnaces.every((furnace:string) => plot.furnaces.includes(furnace))
      );
      return visualizationExists;
    }
  }
  savedPlots(){
    if(!this.usecaseDetail['visualizations']){
      this.usecaseDetail['visualizations'] = [];
    }
    return this.usecaseDetail['visualizations'];
  }
  transformUniqueFolderPaths(data: any[]): { file_path: string }[] {
    const folderPaths = new Set<string>();
  
    data.forEach(item => {
      item.plots.forEach((plot:string) => {
        // Extract folder path by removing the filename
        const folderPath = plot.substring(0, plot.lastIndexOf('/'));
        folderPaths.add(folderPath); // Ensure uniqueness
      });
    });
  
    // Convert the unique paths to the required format
    return Array.from(folderPaths).map(path => ({ file_path: path }));
  }
  
  downloadVisualization(plot:any,download_all:boolean){
    let fileName = '';
    let plots = [];
    if(download_all){
      fileName = this.usecaseDetail.usecase_name+'.zip';
      // plots = this.transformUniqueFolderPaths(this.usecaseDetail['visualizations'])
      let pathsList = this.scenarios
      .filter((scenario: any) => {
        return scenario.results?.excel_result && scenario.results.excel_result.trim() !== '';
      })
      .map((scenario: any) => {
        return { file_path: scenario.results.excel_result.substring(0, scenario.results.excel_result.lastIndexOf('/')) };
      });

      let resultFiles = this.scenarios
      .filter((scenario: any) => {
        return scenario.results?.excel_result && scenario.results?.intermediate_processing?.file_path.trim() !== '';
      })
      .map((scenario: any) => {
        return {
          file_path: scenario.results?.excel_result && scenario.results?.intermediate_processing?.file_path?.substring(0, scenario.results?.intermediate_processing?.file_path.lastIndexOf('/'))
        };      
      });
      if(resultFiles.length){
        pathsList = pathsList.concat(resultFiles); 
      }
      if(pathsList.length>0){
        const uniqueFilePaths = Array.from(
          new Set(pathsList.map((file:any) => file.file_path))
        ).map(file_path => ({ file_path }));
        plots = uniqueFilePaths
      }
    }else{
      fileName = this.usecaseDetail.usecase_name+'_'+plot.alloy+'.zip';
      plots = plot.plots.map((path: any) => {return { file_path:path}});
    }
    if(plots.length>0){
      this.scrapAnalysisService
      .downloadSamFilesData({type:'zip',files:plots})
      .subscribe({
        next: (blob: Blob) =>
          this.handleBlob(blob,fileName),
        error: (error: any) => {
          console.error('Download failed:', error);
          this.errorHandlerService.handleError(error);
        },
      });
    }
  }
    
  private handleBlob(blob: Blob,fileName:string) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }
  
  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
  }

  savePlotConfig(){
    let objToSave = {...this.usecaseDetail};
    let selectedScenarios = this.scenarios.filter((scenario:any)=>(scenario.selected === true && scenario.results?.excel_result && scenario.results.excel_result.trim() !== ''))
    .map((scenario: any) => scenario.scenario_name);    
    if(!objToSave['visualizations']){
      objToSave['visualizations'] = [];
    }
    let plotData = {
      alloy: this.selectedDemand,    
      plots: this.plots,   
      furnaces: selectedScenarios
    }

    const index = this.usecaseDetail['visualizations'].findIndex((visualization: any) =>
      visualization.alloy === this.selectedDemand
    );
    if(index !=-1){
      this.usecaseDetail['visualizations'].splice(index,1)
    }
    objToSave['visualizations'].push(plotData);
    this.scrapAnalysisService
    .saveUsecaseData(objToSave)
    .then((response:any) => {
      if (response) {
        if(response['usecase_id'] && response['usecase_id'] !=''){
          this.usecaseDetail = response['usecase_data'];
          
          this.toaster.success('Visualization saved successfully', '', {
            positionClass: 'custom-toast-position',
          });
        }else{
          this.toaster.error(response['message'], '', {
            positionClass: 'custom-toast-position',
          });
        }
        
      } else{
        this.toaster.error('Failed to save visualization', '', {
          positionClass: 'custom-toast-position',
        });
      }
    })
    .catch((error) => {
      console.error('Failed to get visualization:', error);
      this.toaster.error('Failed to save visualization', error, {
        positionClass: 'custom-toast-position',
      });
    });
  }


  makeDemandSelection(){    
    this.allDemands = this.scenarios.map((scenario: any) => scenario.results?.alloys || []).flat()
      if(this.allDemands.length>0){
        if(!this.usecaseDetail['visualizations']){
          this.usecaseDetail['visualizations'] = [];
        }
        if(this.usecaseDetail['visualizations'] && this.usecaseDetail['visualizations'].length>0){
          let vizData = this.usecaseDetail['visualizations'].filter((viz:any)=>viz.plots.length>0);
          if(vizData.length>0){
            let visualizationData = vizData[vizData.length-1];
            this.selectedDemand = visualizationData.alloy;
            this.plots = visualizationData.plots;
            this.loadingPlot = true;
            for(let i=0;i<this.plots.length;i++){
              this.getImageContent(this.plots[i])
            }
            this.scenarios.forEach(element => {
              if(visualizationData.furnaces.indexOf(element.scenario_name) !=-1){
                element.selected = true;
              }
            });
          }else{
            this.loadDefaultVisualization();
          }          
        }else{
          this.loadDefaultVisualization();
        }        
      }    
  }

  loadDefaultVisualization(){
    this.selectedDemand = this.allDemands[this.allDemands.length-1];
    this.scenarios.forEach(element => {
      var alloyExists = this.disableScenarioSelection(element);
      if(!alloyExists){
        element.selected = true;
      }
    });
    this.plotVisualization();
  }
  ngAfterViewInit() {
    
  }
  selectDefaultScenarios(){
    this.scenarios.forEach((scenario:any)=>{
      if(!this.disableScenarioSelection(scenario)){
        scenario.selected = true;
      }
    })
    this.changeMade = true;
  }
  disableScenarioSelection(scenario:any){
    if(this.selectedDemand !=''){
      const alloyExists = scenario.results?.alloys.some((alloy:string) => alloy === this.selectedDemand);
      if(alloyExists){
        return false;
      }else{
        scenario.selected = false;
        return true
      }
    }else{
      scenario.selected = false;
      return true;
    }
  }

  convertDbObjectToReadable(data: any):any[]{
    return data.scenarios.map((scenario: any, index: number) => ({
      scenario_name: scenario.scenario_name,
      results:scenario.results,
      scraps: this.transformDataSection(scenario.scraps,this.scrapColumns),
      demands: this.transformDataSection(scenario.demands, this.demandColumns),
      limits: this.transformDataSection(scenario.limits, this.limitColumns),
    }));  
  }

  private transformDataSection(data: Record<string, any[]>, columns: string[]): any[] {
    // Assuming that all arrays in `data` have the same length
    const length = data[columns[0]]?.length || 0;
  
    return Array.from({ length }, (_, index) =>
      columns.reduce<Record<string, any>>((acc, column) => {
        acc[column] = data[column]?.[index];
        return acc;
      }, {})
    );
  }

  getImageName(filePath: string): string {
    if (filePath) {
      const parts = filePath.split('/');
      return parts.pop() || ''; // Returns the last part or an empty string if the path is empty
    } else {
      return 'Plot';
    }
  }
  onLoadComplete(){
    this.loadingPlot = false;
  }
  getImageContent(path:string) {
    this.scrapAnalysisService
        .getJSONContent({ path: path.replace('.html', '.json'), name: this.getImageName(path) })
        .subscribe(
          (result) => {
            this.loadingPlot = false;
            this.plotResults.push(JSON.parse(result.content));  
            if(this.plotResults.length==2){
              setTimeout(() => {
                this.drawVizualizationFromJSON()
              }, 50);              
            }
          },
          (error) => {
            console.error('Error fetching image content:', error);
          },
        );
  }

  plotVisualization(){
    if(this.selectedDemand == ''){
      this.toaster.error('Select the demand to plot the vizualiztion', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }

    let selectedScenarios = this.scenarios.filter((scenario:any)=>(scenario.selected === true && scenario.results?.excel_result && scenario.results.excel_result.trim() !== ''))
    .map((scenario: any) => {
      return {
        name: scenario.scenario_name,
        file_path  : scenario.results.excel_result
      }
    });

    if(selectedScenarios.length==0 && !this.baseLineSelect){
      this.toaster.error('Select the scenarios/baseline', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }
    let SamFilePath = ''
    if(this.baseLineSelect){
      let baselinePath = this.scrapAllFiles.filter((file:any)=>file._id==this.usecaseDetail.baseline_file)
      if(baselinePath.length>0){
        SamFilePath = baselinePath[0].custom_information?.sam_result || '';
        selectedScenarios.push({
          name: 'Baseline',
          file_path  : baselinePath[0].custom_information?.sam_result || ''
        });
      }      
    }

    let requestData:any = {
      'scenarios':selectedScenarios,
      'config_path':this.usecaseDetail.config_content,
      'alloy_name': this.selectedDemand, 
      'unit': this.usecaseDetail.unit
    }
    requestData['baseline'] = this.usecaseDetail.baseline_file
    
    // if(SamFilePath == ''){
    //   requestData['baseline'] = this.usecaseDetail.baseline_file
    // }

    this.loadingPlot = true;
    this.plotResults = [];
    this.scrapAnalysisService
    .generatePlot(requestData)
    .then((response:any) => {
      this.changeMade = false;
      if (response) {
        if(response.length>0){
          this.plots = response;
          for(let i=0;i<response.length;i++){
            this.getImageContent(response[i])
          }
        }else{
          this.loadingPlot = false;
          this.toaster.error('Failed to generate the visualization', '', {
            positionClass: 'custom-toast-position',
          });
        }
        
      } else{
        this.loadingPlot = false;
        this.toaster.error('Failed to generate the visualization', '', {
          positionClass: 'custom-toast-position',
        });
      }
    })
    .catch((error) => {
      this.loadingPlot = false;
      this.toaster.error('Failed to generate the visualization', '', {
        positionClass: 'custom-toast-position',
      });
    });
  }


  goToEditScenario(){
    this.editScenarioEvent.emit(this.usecaseDetail);
  }

}
