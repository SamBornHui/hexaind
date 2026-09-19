import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { ToastrService } from 'ngx-toastr';
import { Subject, Subscription } from 'rxjs';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { Router } from '@angular/router';

interface DidConfig {
  [key: string]: string;
}

interface TrainData {
  raw_data_file_path: string;
  all_dids: string[];
  all_design_measurements: any[];
  selected_train_dids: string[];
  selected_test_dids: string[];
  skip_if_exist: boolean;
  save_plots: boolean;
  scaling_coefficient_overloads: any;
  target_material_designation: string[];
  unique_id: string;
  user_id: string;
  updated_at: string;
  path_load_model: string;
}

@Component({
  selector: 'app-uc1-models-predictions',
  templateUrl: './uc1-models-predictions.component.html',
  styleUrls: ['./uc1-models-predictions.component.less'],
})
export class UC1TrainPredictionsComponent implements OnInit, OnDestroy {
  @ViewChild(MatSort) sort!: MatSort;

  private searchTerms = new Subject<string>();
  searchText: string = '';
  selectedWorkflowRow: any = null;
  selectedTab: string = 'train';
  showLoader: boolean | undefined;
  projectId: any;
  aggregateDids: any;
  TrainData: TrainData | null = null;
  predictionData: any;
  selectedFileName: string = '';
  selectedPredictionFileName: string= '';
  selectedFiles: File[] = [];
  fileinput: boolean | undefined;
  isDisabled: boolean = true;
  fileResponse: any;
  didConfig: DidConfig = {};
  rawDataFilePath: string = '';
  uniqueId: string = '';
  userInfo: any;
  user_id: string | undefined;
  selectedUniqueId: string = '';
  predictionUniqueId: string = '';
  uniqueIds: string[] = [];
  predictionConfig: DidConfig = {};
  isSaveDisabled: boolean = true;
  allTrainedDids: string[] = []; // Added
  allPredictionDids: string[] = []
  selected_test_value: boolean = false;
  selected_train_value: boolean = false;
  all_design_measurements: any = [];
  get_design_measurements: string='';
  selected_train_dids: any = [];
  selected_test_dids: any = [];
  toggledidConfig: { [key: string]: string } = {};
  predictionDropdownData : string = '';
  predictionFilePath: any;
  selectedTabIndex: number = 0;

  private projectSubscription: Subscription | undefined = undefined;
  selectedDesignMeasurement: any;
  allDesignMeasurements: any = {};
  selectedPredictionDid: any;
  showMainHeader = false
  toggleHeaderButton: string = 'expand_more';


  constructor(
    private configService: ConfigService,
    private apiService: ApiService,
    public toaster: ToastrService,
    private router: Router,
  ) {}

  ngOnInit() {
    this.projectSubscription = this.configService.selectedProjectIdObservable.subscribe(
      (projectId: any) => {
        if (projectId) {
          this.projectId = projectId;
          this.selectTab(this.selectedTab);
        }
      },
    );
    const user = localStorage.getItem('currentUser');
    this.userInfo = user ? JSON.parse(user) : {};
    this.user_id = this.userInfo?._id;
  }

  ngOnDestroy() {
    if (this.projectSubscription) {
      this.projectSubscription.unsubscribe();
    }
  }

  compareFn = (a: string[], b: string[]) => {
    
    let result  = a.join(',');
    return JSON.stringify(result) === JSON.stringify(b);
  };

  getTrainData(projectId: any) {
    this.isDisabled = true;
    this.selectedFileName =''
    this.apiService.getTrainData(projectId).subscribe(
      (data: TrainData) => {
        this.TrainData = data;
        data.all_design_measurements.map((input)=>{
          this.all_design_measurements.push(input)
        });
        this.selectedDesignMeasurement = data.target_material_designation;
        this.get_design_measurements = data.target_material_designation.toString();
        this.allDesignMeasurements = data.all_design_measurements;
        this.rawDataFilePath = data.raw_data_file_path || '';
        this.uniqueId = data.unique_id || '';
        this.didConfig = this.getInitialDidConfig(data);
        this.allTrainedDids = data.all_dids;
        this.selected_train_value = data.selected_train_dids  ? true : false ;
        this.selected_test_value = data.selected_test_dids  ? true : false ;
        //this.checkIfFieldsAreValid();
      },
      (error) => {
        console.error('Error fetching train data:', error);
        this.TrainData = null;
        this.rawDataFilePath = '';
        this.uniqueId = '';
        this.didConfig = {};
        this.allTrainedDids = [];
      }
    );
  }

  updateValue(event: Event){
      this.selectedDesignMeasurement = event;
      this.checkIfFieldsAreValid();
  }

  setAllTrainedDidsValue(did: string, value: string){
    
    if(value === 'test'){
      for (const key in this.didConfig) {
        if (this.didConfig[key] === 'test') {
          this.didConfig[key] = ''; // Deselect the previous test
        }
      }
    } 

    
    if (this.didConfig[did] === value) {
      this.didConfig[did] = ''; // Deselect if already selected
    } else {
      this.didConfig[did] = value;
    }
    this.checkIfFieldsAreValid();
  }

  isTrainSelected(did: string): boolean {
    return this.didConfig[did] === 'train';
  }

  isTestSelected(did: string): boolean {
    return this.didConfig[did] === 'test';
  }

  getPredictionDropdownData(event : string){
    this.predictionDropdownData = event;
    this.checkPredictionFieldsAreValid();
  }

  // setAllTrainedDidsValue(did: string, value: string): void {
  //   if (value === 'train' || value === 'test') {
  //     this.didConfig[did] = value;
  //   } else {
  //     // Reset if neither 'train' nor 'test' is selected
  //     this.didConfig[did] = null;
  //   }
  // }

  getInitialDidConfig(data: TrainData): DidConfig {
      const didConfig: DidConfig = {};
      (data.all_dids || []).forEach((did: string) => {
        didConfig[did] == '';
      });
      (data.selected_train_dids || []).forEach((did: string) => {
        didConfig[did] = 'train';
      });
      (data.selected_test_dids || []).forEach((did: string) => {
        didConfig[did] = 'test';
      });
      return didConfig;
  }

  getPredictionData(projectId: any) {
    this.apiService.getPredictionData(projectId).subscribe(
      (data) => {
        this.predictionData = data;
        this.selectedUniqueId = data.selected_unique_id || '';
        this.predictionUniqueId = data.prediction_unique_id || '';
        this.predictionDropdownData = data.prediction_did;
        this.predictionFilePath = data.raw_data_file_path;
        this.allPredictionDids = data.all_dids;
        if (this.selectedUniqueId) {
          this.predictionConfig[this.selectedUniqueId] = data.train_did || '';
        }
        //this.checkIfPredictionFieldsAreValid();
      },
      (error) => {
        console.error('Error fetching prediction data:', error);
        this.predictionData = '404';
      }
    );
  }

  selectTab(tab: string) {
    this.selectedTab = tab;
    if (tab === 'train') {
      this.getTrainData(this.projectId);
    } else if (tab === 'predictions') {
      this.getAggregatedConfig(this.projectId);
      this.getPredictionData(this.projectId);
    }
  }

  getAggregatedConfig(projectId: any) {
    this.apiService.getAggregatedConfig(projectId).subscribe(
      (config) => {
        this.aggregateDids = config;
        this.initializeDidConfig();
        this.uniqueIds = config.uniqueIds || [];
      },
      (error) => {
        console.error('Error fetching aggregated config:', error);
      }
    );
  }

  initializeDidConfig() {
    if (this.aggregateDids?.allTrainedDids) {
      this.aggregateDids.allTrainedDids.forEach((did: string) => {
        if (!(did in this.didConfig)) {
          this.didConfig[did] = 'train';
        }
      });
    }
  }

  async onFileSelected(event: any, type: any) {
    const selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.fileinput = true;
    const siteId = this.configService.SelectedSiteId;
    this.selectedFiles = Array.from(event.target.files);
    this.selectedFileName = this.selectedFiles[0]?.name || '';

    if (this.selectedFileName.endsWith('.zip')) {
      const file = this.selectedFiles[0];
      this.showLoader = true;
      if (file) {
        try {
          const response = await this.apiService.GetUploadConfigFiles(file, selectedProjectId, siteId);
          this.fileResponse = response;
          // Assuming the response structure is consistent
          const fileData = response.files[0];
          this.rawDataFilePath = fileData.file_path || '';
          this.allTrainedDids =[];
          this.all_design_measurements=[];
          this.get_design_measurements ='';
          this.TrainData = {
            ...this.TrainData,
            raw_data_file_path: this.rawDataFilePath,
            all_dids: fileData.all_dids,
            all_design_measurements: fileData.all_design_measurements || [],
            selected_train_dids: fileData.selected_train_dids || [],
            selected_test_dids: fileData.selected_test_dids || [],
            skip_if_exist: this.TrainData?.skip_if_exist ?? false,
            save_plots: this.TrainData?.save_plots ?? false,
            scaling_coefficient_overloads: this.TrainData?.scaling_coefficient_overloads || {},
            target_material_designation: this.TrainData?.target_material_designation || [],
            unique_id: this.TrainData?.unique_id ?? '',
            user_id: this.TrainData?.user_id ?? '',
            updated_at: this.TrainData?.updated_at ?? '',
            path_load_model: this.TrainData?.path_load_model ?? '' // Ensure this property is included
          };
          this.didConfig = this.getInitialDidConfig(this.TrainData);
          this.allTrainedDids = this.TrainData.all_dids;
          this.selectedDesignMeasurement= '';
          this.uniqueId = '';
          //this.allPredictionDids = fileData.all_dids;
          this.TrainData.all_design_measurements.map((input)=>{
            this.all_design_measurements.push(input)
          });
          this.checkIfFieldsAreValid();
          this.showLoader = false;
        } catch (error) {
          const err = error as any;
          if (err?.message) {
            this.toaster.error(err?.message, '', {
              positionClass: 'custom-toast-position',
            });
          }
          console.error('Error during file upload:', err.message);
          this.showLoader = false;
          this.isDisabled = true;
        }
      }
    } else {
      alert('Please upload a zip file.');
    }
  }


  async onProdictionFileSelected(event: any, type: any) {
    const selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.fileinput = true;
    this.all_design_measurements=[];
    const siteId = this.configService.SelectedSiteId;
    this.selectedFiles = Array.from(event.target.files);
    this.selectedPredictionFileName = this.selectedFiles[0]?.name || '';

    if (this.selectedPredictionFileName.endsWith('.zip')) {
      const file = this.selectedFiles[0];
      this.showLoader = true;
      if (file) {
        try {
          const response = await this.apiService.GetUploadPredictionConfigFiles(file, selectedProjectId, siteId);
          this.fileResponse = response;
          console.log("response: ", response)
          this.predictionDropdownData = '', 
          this.predictionUniqueId='', 
          this.selectedUniqueId='';
          // Assuming the response structure is consistent
          const fileData = response.files[0];
          this.rawDataFilePath = fileData.file_path || '';
          this.TrainData = {
            ...this.TrainData,
            raw_data_file_path: this.rawDataFilePath,
            all_dids: fileData.all_dids,
            all_design_measurements: fileData.all_design_measurements || [],
            selected_train_dids: fileData.selected_train_dids || [],
            selected_test_dids: fileData.selected_test_dids || [],
            skip_if_exist: this.TrainData?.skip_if_exist ?? false,
            save_plots: this.TrainData?.save_plots ?? false,
            scaling_coefficient_overloads: this.TrainData?.scaling_coefficient_overloads || {},
            target_material_designation: this.TrainData?.target_material_designation || [],
            unique_id: this.TrainData?.unique_id ?? '',
            user_id: this.TrainData?.user_id ?? '',
            updated_at: this.TrainData?.updated_at ?? '',
            path_load_model: this.TrainData?.path_load_model ?? '' // Ensure this property is included
          };
          //this.didConfig = this.getInitialDidConfig(this.TrainData);
          //this.allTrainedDids = fileData.all_dids;
          this.allPredictionDids = fileData.all_dids;
          this.predictionFilePath = fileData.file_path
          this.checkPredictionFieldsAreValid();
          // this.TrainData.all_design_measurements.map((input)=>{
          //   this.all_design_measurements.push(input)
          // });
          // this.checkIfFieldsAreValid();
          this.showLoader = false;
        } catch (error) {
          const err = error as any;
          if (err?.message) {
            this.toaster.error(err?.message, '', {
              positionClass: 'custom-toast-position',
            });
          }
          console.error('Error during file upload:', err.message);
          this.showLoader = false;
          this.isDisabled = true;
        }
      }
      //this.selectTab('predictions');
    } else {
      alert('Please upload a zip file.');
    }
  }


  triggerFileInputClick(fileInput: HTMLInputElement) {
    fileInput.click();
  }

  // checkIfPredictionFieldsAreValid() {
  //   this.isSaveDisabled = false;
  //   // this.isSaveDisabled =  !(this.selectedUniqueId &&
  //   //                         this.predictionUniqueId &&
  //   //                         this.predictionConfig[this.selectedUniqueId]);
  // }

  checkIfFieldsAreValid() {
    const { selected_train_dids, selected_test_dids } = this.separateTrainAndTestData();
    this.isDisabled = !(this.rawDataFilePath && this.selectedDesignMeasurement && this.uniqueId && (selected_train_dids.length > 0));
  }

  checkPredictionFieldsAreValid() {
    this.isSaveDisabled = !(this.predictionDropdownData && this.predictionUniqueId && this.selectedUniqueId);
  }

  saveConfiguration() {
    const { selected_train_dids, selected_test_dids } = this.separateTrainAndTestData();

    const configData = {
      raw_data_file_path: this.rawDataFilePath,
      selected_train_dids,
      selected_test_dids,
      unique_id: this.uniqueId,
      user_id: this.user_id,
      updated_at: new Date().toISOString(),
      all_dids: this.allTrainedDids,
      all_design_measurements: this.all_design_measurements,
      target_material_designation: this.selectedDesignMeasurement,
    };

    this.apiService.saveDidConfig(configData, this.projectId).subscribe(
      (response) => {
        this.toaster.success('Configuration saved successfully');
      },
      (error) => {
        this.toaster.error('Error saving configuration');
      }
    );
  }

  savePredictionConfiguration() {
    const configData = {
      selected_unique_id: this.selectedUniqueId,
      prediction_unique_id: this.predictionUniqueId,
      prediction_did: this.predictionDropdownData,
      user_id: this.user_id,
      raw_data_file_path: this.predictionFilePath,
      all_dids: this.allPredictionDids,
      updated_at: new Date().toISOString(),
    };

    this.apiService.savePredictionConfig(configData, this.projectId).subscribe(
      (response) => {
        this.toaster.success('Prediction configuration saved successfully');
      },
      (error) => {
        this.toaster.error('Error saving prediction configuration');
      }
    );
  }

  separateTrainAndTestData() {
    const selected_train_dids: string[] = [];
    const selected_test_dids: string[] = [];
    for (const did in this.didConfig) {
      if (this.didConfig[did] === 'train') {
        selected_train_dids.push(did);
      } else if (this.didConfig[did] === 'test') {
        selected_test_dids.push(did);
      }
    }
    return { selected_train_dids, selected_test_dids };
  }

  onTabChange(event: MatTabChangeEvent): void {
      this.selectedTabIndex = event.index;
    if (event.index === 0) { // 0 is the index for the "Train" tab
      this.getTrainData(this.projectId);
    } else {
      this.getPredictionData(this.projectId);
      this.getAggregatedConfig(this.projectId);
    }
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

  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

}
