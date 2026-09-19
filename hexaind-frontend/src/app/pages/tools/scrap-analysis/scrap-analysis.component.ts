import {
  ChangeDetectorRef,
  Component,
  OnInit,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import * as Plotly from 'plotly.js-dist-min';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { environment } from 'src/environments/environment';
import { ToastrService } from 'ngx-toastr';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { MatDialog } from '@angular/material/dialog';

import { ScrapAnalysisService } from './services/scrap-analysis.service'




@Component({
  selector: 'app-scrap-analysis',
  templateUrl: './scrap-analysis.component.html',
  styleUrls: ['./scrap-analysis.component.less'],
})

export class ScrapAnalysisComponent implements OnInit {
  view:string = '';
  showMainHeader:boolean = false;
  toggleHeaderButton: string = 'expand_more';
  editScenaro: boolean = false;

  subComponents: any[] = [
    {title:'Create New Scenarios', value:'scenarios',disabled:false, show:true},
    {title:'View Scenario Runs', value:'runs',disabled:false, show:true},
    {title:'View Baseline Files', value:'files',disabled:false, show:true},
    {title:'Run Vizualization', value:'vizualization',disabled:false, show:false}
  ];

  useCasesList:any[] = []; 
  scrapAllFiles:any[] = [];
  plotResult:any = {};
  useCaseDetail:any = {} 
  isNavCollapsed: boolean = false;
  usecaseVisualization:any = {}
  selectedBaseline:string = ''
  loadingPlot: boolean = false;
  fromView: string = ''
  

  constructor(
    private cd: ChangeDetectorRef,
    private http: HttpClient,
    private snackBarNotificationService: SnackBarNotificationService,
    private configService: ConfigService,
    private router: Router,
    public toaster: ToastrService,
    private errorHandlerService: ErrorHandlerService,
    public dialog: MatDialog,
    private scrapAnalysisService:ScrapAnalysisService
  ) {
  }

  ngOnInit() {
    this.fetchUploadedFiles()
    this.fetchUseCases();
  }

  setDefaultSelectedBaseline(){
    if(this.selectedBaseline !=''){
      this.loadingPlot = true;
      this.plotResult = {};
      this.scrapAnalysisService
      .generatePlot(this.selectedBaseline)
      .then((response:any) => {
        if (response) {
          if(response.plot){
            this.plotResult = response.plot;
            this.drawBaselineVisualization();
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
    
  }

  adminUploadedBaseline(){    
    return this.scrapAllFiles.filter((element:any)=>(element.tags.includes('upload') && element.tags.includes('admin_upload')));
  }

  drawBaselineVisualization(){
    Plotly.newPlot('baselineplot', this.plotResult.data, this.plotResult.layout)
  }

  viewRunScenarios(event:any){
    if(event.view =='vizualization'){
      this.fromView = event.from_view;
      this.usecaseVisualization = event.data;
      this.view = 'vizualization'
    }else if(event.view =='runs'){
      this.fromView = event.from_view;
      this.view = 'runs'
    }    
  }

  fetchUseCases(){
    this.scrapAnalysisService
      .getUseCasesData()
      .then((response) => {
        if (response) {
          this.useCasesList = response;
          // this.view = 'runs'
        }
      })
      .catch((error) => {
        console.error('Failed to get usecases:', error);
    });
  }

  fetchUploadedFiles(){
    this.scrapAnalysisService
    .getUploadedFiles()
    .then((response) => {
      if (response) {
        if(response.datasets){
          this.scrapAllFiles = response.datasets;          
          if(this.scrapAllFiles.length==0){
            this.view = 'main'       
            let index = this.subComponents.findIndex((view:any)=>view.value=='scenarios')
            if(index !=-1){
              this.subComponents[index].disabled = true;
            }
          }else{
            this.view = 'scenarios'
          }          
        }
      } 
    })
    .catch((error) => {
      console.error('Failed to get files:', error);
    });
  }

  useCaseEvent(usecases:any){
    this.useCasesList = usecases;
  }

  baselineFileEvent(event:any){
    this.scrapAllFiles = event;
    let index = this.subComponents.findIndex((option)=>option.value === 'scenarios')
    if(index != -1){
      this.subComponents[index].disabled = false;
    }
  }
  
  editScenarioEvent(event:any){
    this.view ='scenarios'
    this.editScenaro = true;
    this.useCaseDetail = event
  }

  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

  goBack(){
    if(this.view=='main'){
      const selectedProjectId = this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
      const projectId = selectedProjectId;
      const siteId = this.configService.SelectedSiteId;
      this.router.navigate([`sites/${siteId}/projects/${projectId}/tools`]);
    }else if(this.view =='vizualization'){
      if(this.fromView == 'runs'){
        this.view = 'runs'
      }else if(this.fromView == 'scenarios'){
        this.view = 'scenarios'
      }      
    }else{
      if(this.view =='scenarios'){
        this.editScenaro = false;
        this.useCaseDetail = {}
        this.view = 'main'
        // this.setDefaultBaseline()
      }else{
        this.view = 'main'
        // this.setDefaultBaseline()
      }      
    }
  }
  setDefaultBaseline(){
    let baselines = this.scrapAllFiles.filter((element:any)=>(element.tags.includes('upload') && element.tags.includes('admin_upload')));
    if(baselines.length>0){
      this.selectedBaseline = baselines[0]._id;
      this.setDefaultSelectedBaseline()
    }
  }
  
  currentView(){
    if(this.view=='main' || this.view==''){
      return 'Scrap Analysis'
    }else{
      let component = this.subComponents.filter((val:any)=>val.value==this.view);
      return component[0].title
    }
  }

  navigate(view:string){
    if(view=='scenarios'){
      this.editScenaro = false
    }    
    this.view = view; 
  }

}
