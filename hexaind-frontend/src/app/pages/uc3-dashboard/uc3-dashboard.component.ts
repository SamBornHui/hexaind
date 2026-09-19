import {
  Component,
} from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'filteredItems',
  pure: true,
})
export class FilteredItemsPipe implements PipeTransform {
  transform(items: any[], filter: string, isKeyValueArray: boolean): any[] {
    if (!items || !filter) {
      return items;
    }
    return items.filter((item:any) => {
      if(isKeyValueArray)  return item.value.toLowerCase().includes(filter.toLowerCase())
      return item.toLowerCase().includes(filter.toLowerCase())
    })
  }
}

@Component({
  selector: 'app-uc3-dashboard',
  templateUrl: './uc3-dashboard.component.html',
  styleUrls: ['./uc3-dashboard.component.less'],
})
export class Uc3DashboardComponent {
  showMainHeader: boolean = true;
  flexValue = 'calc(100% - 334px)';
  rgtNavToggle: boolean = false;
  isDataLoaded: boolean = false;
  toggleHeaderButton: string = 'expand_more';
  workFlowList: any = [];
  runs: any = [];
  topFeatures: any = [];
  stepNames: any = [];
  selectedWorkflow: any;
  selectedRun: any;
  selectedTopFeature: any;
  selectedStepName: any;
  selectedPreviewType: any;
  runsPlotData: any;
  topFeatureData: any;
  stepNameData: any;
  isRunPlotDisabled: boolean = false;
  isTopFeatureDataDisabled: boolean = false;
  isStepNameDataDisabled: boolean = false;
  rootDirectory = "";
  isFetchingStepPlots = false
  workflowFilter: any;
  runFilter: any;
  stepFilter: any;
  topFeatureFilter: any;
  selectedRunId: any;
  selectedWorkflowId: any;

  constructor(
    private configService: ConfigService,
    private router: Router,
    private apiService: ApiService,
    private sanitizer: DomSanitizer,
    public toaster: ToastrService
  ) {}

  ngOnInit() {
    this.getWorkflowNames();
  }

  async getWorkflowNames() {
    this.workFlowList = await this.apiService.getUC3DashboardWorkflows();
    this.workFlowList = this.convertObjectToArray(this.workFlowList);
  }

  async onWorkflowChange($event: any) {
    this.reset()
    this.selectedWorkflow = $event.option.value;
    this.selectedWorkflowId = this.workFlowList.find((element:any) => element.value === this.selectedWorkflow).key;
    this.runs = await this.apiService.getUC3DashboardRuns(
      this.selectedWorkflowId,
    );
    this.runs = this.convertObjectToArray(this.runs)
  }

  async onRunChange($event: any) {
    this.selectedRun = $event.option.value
    this.selectedRunId = this.runs.find((element:any) => element.value === this.selectedRun).key;
    this.selectedPreviewType = 'Run';
    this.selectedTopFeature = ""
    this.topFeatures = []
    this.topFeatureData = []
    this.selectedStepName = ""
    this.stepNames = []
    this.stepNameData = []
    let response: any;
    try {
      response = await this.apiService.getUC3DashboardMetadata(
        this.selectedRunId
      );
    }   
    catch(error) {
      this.toaster.error('No plots present for this step', '', {
        positionClass: 'custom-toast-position',
      });
    }
    this.topFeatures = response.feature_names
    this.stepNames = response.step_names;
    this.rootDirectory = response.root_directory
    this.loadSelectedTabPlots();
    this.isDataLoaded = true;
  }

  async onTopFeaturesChange($event: any) {
    this.selectedTopFeature = $event.option.value;
    this.selectedPreviewType = 'Top Features';
    this.selectedStepName = ""
    this.loadSelectedTabPlots();
  }

  onStepNameChange($event: any) {
    this.selectedStepName = $event.option.value;
    this.selectedPreviewType = 'Step Names';
    this.loadSelectedTabPlots();
  }

  async loadSelectedTabPlots() {
    if (this.selectedPreviewType === 'Run') {
      this.runsPlotData = {};
      let featureImportancePlotFile =
        this.rootDirectory + '/SHAP' + '/shap_beeswarm_plot.svg';
      let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
        `${this.configService.getAppAuxApiURL}/eda/file?path=${featureImportancePlotFile}`,
      );
      this.runsPlotData = {
        completeUrl,
        isLoaded: false,
      };
    }

    if (this.selectedPreviewType === 'Top Features') {
      this.topFeatureData = [];
      let scatterPlotUrl =
        this.rootDirectory +
        '/SCATTER_PDP' +
        `/${this.selectedTopFeature}_scatter.html`;
      let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
        `${this.configService.getAppAuxApiURL}/eda/file?path=${scatterPlotUrl}`,
      );
      this.topFeatureData.push({
        completeUrl,
        isLoaded: false,
      });

      let pdpPlotUrl =
        this.rootDirectory +
        '/SCATTER_PDP' +
        `/${this.selectedTopFeature}_pdp.html`;
      completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
        `${this.configService.getAppAuxApiURL}/eda/file?path=${pdpPlotUrl}`,
      );
      this.topFeatureData.push({
        completeUrl,
        isLoaded: false,
      });
    }

    if (this.selectedPreviewType === 'Step Names') {
      let stepPlotPaths:any = []
      try {
        this.isFetchingStepPlots = true
        stepPlotPaths = await this.apiService.getUC3DashboardStepPlotPaths(
          this.selectedStepName,
          this.selectedTopFeature,
          this.selectedRunId
        );
        this.isFetchingStepPlots = false
      }
      catch(error) {
        this.toaster.error('No plots present for this step', '', {
          positionClass: 'custom-toast-position',
        });
        this.isFetchingStepPlots = false
        return;
      }

      stepPlotPaths.forEach((path: any) => {
        let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${path || ''}`,
        );
        this.stepNameData.push({
          completeUrl,
          isLoaded: false,
        });
      })

      this.toggleRgtNav();
    }
  }

  onRunPlotDataLoad() {
    if (this.runsPlotData) {
      this.runsPlotData.isLoaded = true;
    }
  }

  onTopFeatureDataLoad(currentPath: any) {
    this.topFeatureData.forEach((path: any) => {
      if (currentPath.completeUrl == path.completeUrl) path.isLoaded = true;
    });
  }

  onStepNameDataLoad(currentPath: any) {
    this.stepNameData.forEach((path: any) => {
      if (currentPath.completeUrl == path.completeUrl) path.isLoaded = true;
    });
  }

  async changeViewerFanout(viewerType: any) {
    this.selectedPreviewType = viewerType;
  }

  navigate(pageName: string) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
  }

  toggleRgtNav() {
    this.rgtNavToggle = !this.rgtNavToggle;
    this.flexValue =
      this.flexValue === 'calc(100% - 334px)'
        ? 'calc(100% - 58px)'
        : 'calc(100% - 334px)';
  }

  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

  reset(isTotalReset?:boolean) {

    if(isTotalReset) {
      this.workflowFilter = ""
      this.selectedWorkflow = ""
      this.selectedWorkflowId = ""
    }
    this.runs = [];
    this.topFeatures = [];
    this.stepNames = [];
    this.selectedRun = '';
    this.selectedTopFeature = '';
    this.selectedStepName = '';
    this.selectedRunId = ''
    this.runFilter = ''
    this.topFeatureFilter = ''
    this.stepFilter = ''
    this.runsPlotData = [];
    this.topFeatureData = [];
    this.stepNameData = [];
    this.isDataLoaded = false;
  }

  plotLoadingFailed(metadata: any) {
    metadata.isLoaded = true; 
    metadata.isError = true
  }

  convertObjectToArray(obj: { [key: string]: string }): { key: string, value: string }[] {
    return Object.entries(obj).map(([key, value]) => ({ key, value }));
  }
}
