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
  TemplateRef 
} from '@angular/core';
import {
  HttpClient,
  HttpEventType,
} from '@angular/common/http';
import { ToastrService } from 'ngx-toastr';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ScrapAnalysisService } from '../services/scrap-analysis.service'
import { ChangeDetectorRef } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatMenu, MatMenuTrigger } from '@angular/material/menu';
import { FormControl } from '@angular/forms';
import { Observable } from 'rxjs';
import { startWith, map, catchError } from 'rxjs/operators';
import { SamScenrioTypes } from 'src/app/models/workflow-models'
import * as ini from 'ini';
import { CodeMirrorEditorService } from 'src/app/monaco-editor/codemirror-editor.service';
import { CodeMirrorEditorComponent } from 'src/app/monaco-editor/codemirror-editor.component';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-scrap-scenarios',
  templateUrl: './scrap-scenarios.component.html',
  styleUrls: ['./scrap-scenarios.component.less'],
})

export class scrapScenarioComponent implements OnInit{
  @Input() scrapAllFiles: any;
  @Input() useCaseDetail: any;
  @Input() useCasesList: any;
  @Input() editScenaro: boolean = false;
  @Input() enableRunScenarioButton: boolean = false;
  @Output() useCaseEvent = new EventEmitter();
  @Output() viewRunEvent = new EventEmitter();
  @ViewChild('confirmationDialogTemplate') confirmationDialogTemplate!: TemplateRef<any>;
  dialogRef!: MatDialogRef<any>;
  
  editUsecCaseName:boolean = false; 
  selectedFile: string = '';
  selectedToDisplayFile: string = '';
  case_id: string = '';
  scenarios:any[] = [];

  use_case_name:string = 'Use Case 1';
  use_case_description:string = '';
  edit_case_name:string = '';
  changeMade: boolean = false;

  editScenarioName:boolean = false;
  editScenarioOriginalName:string = '';
  editScenarioNewName:string = '';

  scrapColumns: string[] = [
    'Alloy',
    'Source',
    'Cost',
    'Available Weight',
    'Si',
    'Mg',
    'Cu',
    'Fe',
    'Mn',
    'Cr',
    'Zn',
    'Ti',
    'actions'
  ];

  demandColumns: string[] = [
    'Alloy',
    'Plant',
    'Supply',
    'Si',
    'Mg',
    'Cu',
    'Fe',
    'Mn',
    'Cr',
    'Zn',
    'Ti',
    'actions',
  ];

  limitColumns: string[] = [
    'Plant',
    'Scrap',
    'Demand',
    'Limit',
    'actions',
  ];

  typeMap:any = {
    scrap: 'scraps',
    demand: 'demands',
    limit: 'limits'
  };

  limitTypeMap:any = {
    PLANT: 'PLANT',
    DEMAND: 'DEMAND',
    SCRAP: 'SCRAP'
  };



  scrapsList:any = {}
  scraps:any[] = [];
  allUniqueSources:any[] = [];

  searchScrapControl = new FormControl('');
  filteredScrapAlloys!: Observable<string[]>;
  selectedScrapAlloys: string[] = []; // Store selected alloys


  demandsList:any = {}
  demands:any[] = [];
  allUniqueFurnace:any[] = [];

  searchDemandControl = new FormControl('');
  filteredDemandAlloys!: Observable<string[]>;
  selectedDemandAlloys: string[] = []; // Store selected alloys
  plants: string[] = []; // Store selected alloys
  scrapFilePath:string = '';
  demandFilePath:string = '';


  // Limit parameters 
  limitPlantSearchControl = new FormControl('');
  limtitFilteredPlants!: Observable<string[]>;
  filteredLimitScrapAlloys!: Observable<string[]>;
  filteredLimitDemandAlloys!: Observable<string[]>;
  limitSelectedPlants: string[] = []; // Store selected plants

  limitScrapSearchControl = new FormControl('');
  limitSelectedScraps: string[] = []; // Store selected scraps

  limitDemandSearchControl = new FormControl('');
  limitSelectedDemands: string[] = []; // Store selected demands
  usecase_id: string = '';
  currentUser:any = {}
  expandedAccrodian:number = 0;
  runScenario: boolean = false;

  @ViewChildren(MatMenuTrigger) menuTriggers!: QueryList<MatMenuTrigger>;

  @ViewChild('limitPlantMenuTrigger') limitPlantMenuTrigger!: MatMenuTrigger;
  @ViewChild('limitScrapMenuTrigger') limitScrapMenuTrigger!: MatMenuTrigger;
  @ViewChild('limitDemandMenuTrigger') limitDemandMenuTrigger!: MatMenuTrigger;

  // @HostListener('document:click', ['$event'])
  // onDocumentClick(event: Event): void {
  //   const clickedInside = (event.target as HTMLElement).closest('.mat-menu-trigger, .mat-menu-panel, .trigger-icon, input[matInput], .sa-custom-input');
  //   // If the click is outside the menus and their triggers, close all menus
  //   if (!clickedInside) {
  //     this.closeAllMenus();
  //   }
  // }

  config_content: string='';
  savedResponse:any;
  config_file_name:string = '';
  defaultConfigFile:string = '';

  selectedFileMenu:string = 'admin_upload';
  filterFileMenuList: any[] = [
    {title:'All', value:'all'},
    {title:'Uploaded', value:'upload'},
    {title:'Scenario Runs', value:'scenario_run'},
    {title:'Admin Uploaded', value:'admin_upload'}
  ];
  searchText:string = '';
  limitsData:any = {}

  limitBySelected:string = 'NONE';
  limitsOptions:any = [
    {title:'Plant source',value:'PLANT',list:['Plant','Scrap','Demand','Limit']},
    {title:'Scrap alloy',value:'SCRAP',list:['Scrap','Plant','Demand','Limit']},
    {title:'Demand alloy',value:'DEMAND',list:['Demand','Plant','Scrap','Limit']}
  ]




  constructor(
    private http: HttpClient,
    public toaster: ToastrService,
    private configService: ConfigService,
    private router: Router,
    private errorHandlerService: ErrorHandlerService,
    private scrapAnalysisService: ScrapAnalysisService,
    private cdr: ChangeDetectorRef,
    private codeMirrorEditorService:CodeMirrorEditorService,
    private dialog:MatDialog
  ) {
  }

  ngOnInit(): void {    
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);  
    if(this.editScenaro){
      this.enableRunScenarioButton = true;
      this.readScenarioData();
    }else{      
      this.addRandomUsecasename();
      this.setDefaultBaseline();
    }
  }

  transformLimitHeader(column:string){
    return (column =='Plant')?'Source':column
  }

  getSelectedLimitList(){
    return (this.limitBySelected !='NONE')?this.limitsOptions.filter((limit:any)=>limit.value==this.limitBySelected)[0].list:[];
  }

  onExpandedChange(isExpanded: boolean, index: number): void {
    if(isExpanded){
      this.expandedAccrodian = index;
    }
  }

  limitBy(value:string){
    this.limitBySelected = value; 
    this.scenarios[this.expandedAccrodian].limit_by = value;

    // Close the mat-menu on change limit by   
    this.limitPlantMenuTrigger?.closeMenu();
    this.limitScrapMenuTrigger?.closeMenu();
    this.limitDemandMenuTrigger?.closeMenu();

    // this.limitColumns = this.getSelectedLimitList().concat(['actions'])
    let selLimitColumns = this.limitsOptions.filter((limit:any)=>limit.value==this.scenarios[this.expandedAccrodian].limit_by)[0].list
    this.limitColumns = selLimitColumns.concat(['actions'])


    this.limitSelectedPlants = [];
    this.limitSelectedScraps = [];
    this.limitSelectedDemands = [];
    this.limtitFilteredPlants = this.limitPlantSearchControl.valueChanges.pipe(
      startWith(''),
      map(value => this.filterLimitsListAlloys(value || '', SamScenrioTypes.Plant))
    );

    this.filteredLimitScrapAlloys = this.limitScrapSearchControl.valueChanges.pipe(
      startWith(''),
      map(value => this.filterLimitsListAlloys(value || '',SamScenrioTypes.Scrap))
    );
  }

  extractLimitsData(){   
    let base_path = this.scrapAllFiles.filter((file:any)=>file._id==this.selectedFile)[0].dataset_location[0].path; 
    if(base_path && base_path !=''){
      this.scrapAnalysisService
      .getFormatLimitsData(base_path)
      .then((response) => {
        if (response) {
          this.limitsData = response
         
          this.limtitFilteredPlants = this.limitPlantSearchControl.valueChanges.pipe(
            startWith(''),
            map(value => this.filterLimitsListAlloys(value || '', SamScenrioTypes.Plant))
          );
  
          this.filteredLimitScrapAlloys = this.limitScrapSearchControl.valueChanges.pipe(
            startWith(''),
            map(value => this.filterLimitsListAlloys(value || '',SamScenrioTypes.Scrap))
          );
          
          this.filteredLimitDemandAlloys = this.limitDemandSearchControl.valueChanges.pipe(
            startWith(''),
            map(value => this.filterLimitsListAlloys(value || '',SamScenrioTypes.Demand))
          );
        } 
      })
      .catch((error) => {
        console.error('Failed to get files:', error);
      });  
    }
  }

  private filterLimitsListAlloys(value: string, type:string): string[] {
    let filterValue = value.toLowerCase();
    let list = this.getSelectedLimitList();
    if(type==SamScenrioTypes.Scrap){      
      if(list[0]==='Plant' || (list[0]==='Demand' && list[1]==='Plant')){
        return this.limitsData.limits
        .filter((limit:any) => limit.Plant === this.limitSelectedPlants[0] && limit.Alloy.toLowerCase().includes(filterValue))
        .map((limit:any)=>limit.Alloy)
        .filter((value:string, index:number, self:any) => 
          self.findIndex((v:any) => v === value) === index  // Ensure uniqueness by checking the plant value
        );
      }else{
        return this.limitsData.limits
        .filter((limit:any) => (limit.Alloy ?? '').toString().toLowerCase().includes(filterValue))
        .map((limit:any)=>limit.Alloy)
        .filter((value:string, index:number, self:any) => 
          self.findIndex((v:any) => v === value) === index  // Ensure uniqueness by checking the plant value
        );
      }      
    }else if(type==SamScenrioTypes.Demand){
      // const uniqueKeys:any[] = [
      //   ...new Set(
      //     this.limitsData.limits.flatMap((obj:any) => Object.keys(obj).filter(key => key !== 'Plant' && key !== 'Alloy'))
      //   )
      // ];
      // return uniqueKeys;
      return this.limitsData.demands.filter((demand:string) => demand.toLowerCase().includes(filterValue));
      
      // return this.limitsData.demands.filter((demand:string) => demand.toLowerCase().includes(filterValue));
    }else if(type==SamScenrioTypes.Plant){
      if(list[0]==='Scrap'){
        return this.limitsData.limits
        .filter((limit:any) => limit.Alloy === this.limitSelectedScraps[0] &&limit.Plant.toLowerCase().includes(filterValue))
        .map((limit:any)=>limit.Plant)
        .filter((value:string, index:number, self:any) => 
          self.findIndex((v:any) => v === value) === index  // Ensure uniqueness by checking the plant value
        );
      }else{
        return this.limitsData.limits
        .filter((limit:any) => (limit.Plant ?? '').toString().toLowerCase().includes(filterValue))
        .map((limit:any)=>limit.Plant)
        .filter((value:string, index:number, self:any) => 
          self.findIndex((v:any) => v === value) === index  // Ensure uniqueness by checking the plant value
        );
      }
      
    }else{
      return [];
    }
  }

  onSelectPlant(){
    
  }


  showEditModeOption(){
    return (this.usecase_id !='')?true:false
  }
  disabledEvent(){
    return (this.usecase_id !='' && this.changeMade == false)
  }
  toggleLock(){
    this.changeMade = !this.changeMade;
  }

  setDefaultBaseline(){
    let files = this.scrapAllFiles.filter((element:any)=>element.tags.includes('admin_upload')).sort((a:any, b:any) => {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
    if(files.length>0){
      this.selectedToDisplayFile = files[0]._id;
      this.getFormatScrapData(this.selectedToDisplayFile,true);
    }
  }
  onPaste(event: ClipboardEvent,tableRow:any) {
    event.preventDefault();
    const clipboardData = event.clipboardData?.getData('text');
    if (clipboardData) {
      tableRow = this.processPastedData(clipboardData,tableRow);
    }
  }
  processPastedData(data: string,tableRow:any) {
    const rows:any = data.split('\n').map(row => row.split('\t'));
    let columns = [
      'Available Weight',
      'Si',
      'Mg',
      'Cu',
      'Fe',
      'Mn',
      'Cr',
      'Zn',
      'Ti'
    ]
    let coppiedData = rows;
    if(rows.length==1){
      coppiedData = rows[0]
    }
    if(coppiedData.length==8){
      columns.splice(0,1)
    }
    for(let i=0;i<columns.length;i++){
      if (Array.isArray(coppiedData[i])) {
        tableRow[columns[i]] = parseFloat(coppiedData[i][0]);
      } else {
        tableRow[columns[i]] = parseFloat(coppiedData[i]);
      }
    }
    return tableRow;
  }
  // addDefaultConfig(editMode:boolean){
  //   this.scrapAnalysisService.readConfig().subscribe(
  //     (data) => {
  //       this.config_content = JSON.stringify(data);
  //     },
  //     (error) => {
  //       console.error('Error loading config:', error);
  //     }
  //   );
  // }

  getDefaultConfigFile() {
    this.scrapAnalysisService
    .getDefaultConfigFile()
    .then((response) => {
      if (response) {
        this.defaultConfigFile = response.config_file
      } 
    })
    .catch((error) => {
      console.error('Failed to get files:', error);
    });
  }

  closeAllMenus(): void {
    // Close all open menus
    this.menuTriggers.forEach(trigger => {
      if (trigger.menuOpen) {
        trigger.closeMenu();
      }
    });
  }
  
  disableBaselineSelection() {
    if (!this.usecase_id) return false;
    return this.scenarios.some(scenario => scenario.results?.excel_result?.trim());
  }
  


  // getFileContent() {
  //   let siteId = this.configService.SelectedSiteId;
  //   let selectedProjectId: string | undefined = this.configService.SelectedProjectId;

  //   if (!siteId || !selectedProjectId) {
  //     return undefined;
  //   }
  //   const data = {
  //     file_path: this.config_content,
  //     file_name: 'config.ini'
  //   };

  //   return this.codeMirrorEditorService.getFileContent(siteId, selectedProjectId, data);
  // }

  // openNewConfigView(content:any){
  //   this.dialog.open(CodeMirrorEditorComponent, {
  //     width: '90%',
  //     height: '90%',
  //     data: {
  //       content: content,
  //       mode: 'text/x-ini'
  //     },
  //   });
  // }

  // openFileContentDialog() {
  //   if (this.config_content.endsWith('.ini')) {
  //     const data = {
  //       file_path: this.config_content,
  //       file_name: 'config.ini'
  //     };

  //     this.scrapAnalysisService
  //     .readConfigFileData(data)
  //     .subscribe(
  //       (result) => {
  //         if(result.content){
  //           this.openNewConfigView(JSON.parse(result.content))
  //         }
  //       },
  //       (error) => {
  //         console.error('Error fetching image content:', error);
  //       },
  //     );
  //   }else{
  //     this.openNewConfigView(JSON.parse(this.config_content))
  //   }
  // }
  
  expandScenario(index:number){
    this.expandedAccrodian = index;
    this.limitBySelected = 'NONE';
    // this.limitBySelected = (this.scenarios[this.expandedAccrodian].limit_by)?this.scenarios[this.expandedAccrodian].limit_by:''
  }

  viewScenarioRun(){
    this.viewRunEvent.emit({view:'vizualization',data:this.useCaseDetail,from_view:'scenarios'});
  }

  goScenarioRuns(){
    this.viewRunEvent.emit({view:'runs'});
  }
 
  // onFileSelected(event: Event): void {
  //   try {
  //     const fileInput = event.target as HTMLInputElement;
  //     const file = fileInput?.files?.[0];
  
  //     if (!file) {
  //       throw new Error('No file selected. Please select a file.');
  //     }
  //       // Optional: Check file type
  //     this.config_file_name = file.name;
  //     const reader = new FileReader();
  
  //     reader.onload = (e) => {
  //       try {
  //         const content = e.target?.result as string;
  //         this.config_content = JSON.stringify(content);  // You might want to do further parsing based on your use case.
  //         // this.changeMade = true;
  //         this.toaster.success('Config file uploaded successfully!', '', {
  //           positionClass: 'custom-toast-position',
  //         });
  //       } catch (readerError) {
  //         // Handle errors during the FileReader onload
  //         this.toaster.error('Error reading the file.', '', {
  //           positionClass: 'custom-toast-position',
  //         });
  //         console.error('FileReader error:', readerError);
  //       }
  //     };
  
  //     // Trigger file reading
  //     reader.onerror = (err) => {
  //       this.toaster.error('Error reading the file.', '', {
  //         positionClass: 'custom-toast-position',
  //       });
  //       console.error('FileReader error:', err);
  //     };
  
  //     reader.readAsText(file);
  //   } catch (error) {
  //     // Catch any other errors (e.g., no file selected or invalid file type)
  //     this.toaster.error('Error reading the file', '', {
  //       positionClass: 'custom-toast-position',
  //     });
  //     console.error('Error:', error);
  //   }
  // }
  addRandomUsecasename(){
    let newScenarioName = '';
    let counter = 1;
    // Check if the name already exists, and keep incrementing if necessary
    do {
      newScenarioName = `Use Case ${counter}`;
      counter++;
    } while (this.useCasesList.some((usecase:any) => usecase.usecase_name === newScenarioName));
    this.use_case_name = newScenarioName;
  }

  displayFilteredFiles(){
    if(this.selectedFileMenu=='all'){
      return this.scrapAllFiles;
    }else if(this.selectedFileMenu=='upload'){
      return this.scrapAllFiles.filter((element:any)=>(element.tags.includes('upload') && !element.tags.includes('admin_upload')));
    }else{
      return this.scrapAllFiles.filter((element:any)=>element.tags.includes(this.selectedFileMenu));
    }
  }

  readScenarioData(){
    this.usecase_id = this.useCaseDetail.usecase_id;
    this.use_case_name = this.useCaseDetail.usecase_name;
    this.selectedFile = this.useCaseDetail.baseline_file;
    this.selectedToDisplayFile = this.useCaseDetail.baseline_file;
    this.use_case_description = this.useCaseDetail.usecase_desc;
    this.scenarios = this.convertDbObjectToReadable(this.useCaseDetail);
   
    setTimeout(() => {
      this.setSourcePlantUpdate()
      this.getFormatScrapData(this.selectedFile,true);
    }, 50);
    
  }
  setSourcePlantUpdate(){
    this.scenarios.forEach((scenario:any)=>{
      scenario.scraps.forEach((scrap:any)=>{
        if(scrap.Source ==''){
          scrap.new = true;
        }
      })
      scenario.demands.forEach((demand:any)=>{
        if(demand.Plant ==''){
          demand.new = true;
        }
      })
    })
  }
  // disableResetConfig(){
  //   if(this.config_content == ''){
  //     return true;
  //   }else{
  //     return false
  //   }
  // }

  getUncompltedScraps(){   
    let alloys = this.scenarios
      .map((scenario: any) => 
        scenario.scraps
          .filter((scrap: any) => scrap['Source'] === '')  // Filter scraps with empty Source
          .map((item: any) => item.Alloy)  // Map to get the Alloy values
      )
      .flat();  // Flatten the array to get a single list of alloys
    if(alloys.length>0){
      let base_path = this.scrapAllFiles.filter((file:any)=>file._id==this.selectedFile)[0].dataset_location[0].path; 
      let inputData:any = {
        baseline_file:base_path,
        alloys:[],
        file_path:''
      }
      inputData.alloys = alloys;
      inputData.file_path = this.scrapFilePath;
      if(inputData.alloys.length>0){
        this.scrapAnalysisService
        .getFormatScrapDetailData(inputData)
        .then((response) => {
          if (response) {
            this.scrapsList = Object.assign({}, this.scrapsList, response.extracted_data);
          } 
          this.scenarios.forEach((scenario:any)=>{
            scenario.scraps.forEach((scrap:any) => {
              if(scrap['Source'] == ''){
                scrap['Source'] = [];
                scrap['new'] = true;
              }
            });  
          })  
        })
        .catch((error) => {
          console.error('Failed to get files:', error);
        });
  
      }
    }  
    
  }

  convertDbObjectToReadable(data: any):any[]{
    return data.scenarios.map((scenario: any, index: number) => ({
      scenario_name: scenario.scenario_name,
      results:scenario.results,
      scraps: this.transformDataSection(scenario.scraps,this.scrapColumns),
      demands: this.transformDataSection(scenario.demands, this.demandColumns),
      limits: this.transformDataSection(scenario.limits, this.limitColumns),
      limit_by: (scenario.limit_by)?scenario.limit_by:'NONE'
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

  
  getFormatScrapData(id:string,option?: boolean){
    if(this.selectedToDisplayFile !='' && this.usecase_id =='' && this.scenarios.length==0){
      this.addNewscenario();
    } 

    if(!option){
      if(this.scenarios.length>0){
        let dataAvailable = this.scenarios.filter(scenario => (scenario.scraps.length>0 || scenario.demands.length>0 || scenario.limits.length>0))
        if(dataAvailable.length>0){
          this.dialogRef = this.dialog.open(this.confirmationDialogTemplate, {
            width: '400px'  // Set the width to whatever you prefer
          });      
        }else{
          this.selectedFile = id;
          this.selectedToDisplayFile = id;
          this.getBaselineFileData(id,false)
          this.extractLimitsData()
        }
      }
    }else{
      this.selectedFile = id;
      this.selectedToDisplayFile = id;
      this.getBaselineFileData(id,option)
      this.extractLimitsData()
    }
    
  }


  changeBaseLine(){
    this.scenarios.forEach((scenario:any)=>{
      scenario.scraps = [];
      scenario.demands = [];
      scenario.limits = [];
      scenario.results = {}
    });

    this.getBaselineFileData(this.selectedFile,false)
    this.dialogRef.close();
  }

  cancelConfirmation(){
    this.selectedToDisplayFile = this.selectedFile;
    this.dialogRef.close();
  }
  selectAllLimitOptions(type:string){
    if(type == SamScenrioTypes.Plant){
      let plants = this.filterLimitsListAlloys(this.limitPlantSearchControl.value || '', SamScenrioTypes.Plant)
      this.limitSelectedPlants = [...plants];  
    }else if(type == SamScenrioTypes.Scrap){
      let scraps = this.filterLimitsListAlloys(this.limitScrapSearchControl.value || '', SamScenrioTypes.Scrap)
      this.limitSelectedScraps = [...scraps];  
    }else if(type == SamScenrioTypes.Demand){
      let demands = this.filterLimitsListAlloys(this.limitDemandSearchControl.value || '', SamScenrioTypes.Demand)
      this.limitSelectedDemands = [...demands];  
    }
  }

  getBaselineFileData(id:string,option: boolean){
    let path = this.scrapAllFiles.filter((file:any)=>file._id==id)[0].dataset_location[0].path;
    this.scrapAnalysisService
    .getFormatScrapData(path)
    .then((response) => {
      if (response) {
        this.scrapFilePath = response.scrap_file_path;
        this.demandFilePath = response.demand_file_path;
        this.scraps = response.scrap_alloys.map(String);
        this.allUniqueSources = response.sources.map(String);

        this.demands = response.demand_alloys.map(String);
        this.allUniqueFurnace = response.furnaces.map(String);

        this.plants = [...this.allUniqueSources];

        this.filteredScrapAlloys = this.searchScrapControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterListAlloys(value || '',SamScenrioTypes.Scrap))
        );
        
        this.filteredDemandAlloys = this.searchDemandControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterListAlloys(value || '',SamScenrioTypes.Demand))
        );

        // this.limtitFilteredPlants = this.limitPlantSearchControl.valueChanges.pipe(
        //   startWith(''),
        //   map(value => this.filterListAlloys(value || '', SamScenrioTypes.Plant))
        // );

        // this.filteredLimitScrapAlloys = this.limitScrapSearchControl.valueChanges.pipe(
        //   startWith(''),
        //   map(value => this.filterListAlloys(value || '',SamScenrioTypes.Scrap))
        // );
        
        // this.filteredLimitDemandAlloys = this.limitDemandSearchControl.valueChanges.pipe(
        //   startWith(''),
        //   map(value => this.filterListAlloys(value || '',SamScenrioTypes.Demand))
        // );
        if(option){
          setTimeout(() => {
            this.getUncompltedScraps()
          }, 50);
        }

        if(this.usecase_id !=''){
          this.addNewlyAddedAlloys();
        }

      } 
    })
    .catch((error) => {
      console.error('Failed to get files:', error);
    });
  }

  addNewlyAddedAlloys(){
    let scraps = [];
    let demands = [];
    this.scenarios.forEach((scenario:any)=>{
      if(scenario.demands.length>0){
        for(let i=0;i<scenario.demands.length;i++){
          let demandIndex = this.demands.findIndex((demand:string)=>demand==scenario.demands[i].Alloy);
          if(demandIndex == -1){
            this.demands.push(scenario.demands[i].Alloy);
            demands.push(scenario.demands[i].Alloy);
          }
        }

        this.filteredDemandAlloys = this.searchDemandControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterListAlloys(value || '',SamScenrioTypes.Demand))
        );
        this.filteredLimitDemandAlloys = this.limitDemandSearchControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterLimitsListAlloys(value || '',SamScenrioTypes.Demand))
        );

      }

      if(scenario.scraps.length>0){
        for(let i=0;i<scenario.scraps.length;i++){
          let demandIndex = this.scraps.findIndex((scrap:string)=>scrap==scenario.scraps[i].Alloy);
          if(demandIndex == -1){
            this.scraps.push(scenario.scraps[i].Alloy);
            scraps.push(scenario.scraps[i].Alloy);
          }
        }

        this.filteredScrapAlloys = this.searchScrapControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterListAlloys(value || '',SamScenrioTypes.Scrap))
        );
        this.filteredLimitScrapAlloys = this.limitScrapSearchControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterLimitsListAlloys(value || '',SamScenrioTypes.Scrap))
        );
      }

    });
  }

  private filterListAlloys(value: string, type:string): string[] {
    let filterValue = value.toLowerCase();
    if(type==SamScenrioTypes.Scrap){
      return this.scraps
      .filter(alloy => alloy.toLowerCase().includes(filterValue));

    }else if(type==SamScenrioTypes.Demand){
      return this.demands
      .filter(alloy => alloy.toLowerCase().includes(filterValue));
    }else if(type==SamScenrioTypes.Plant){
      return this.plants
      .filter(alloy => alloy.toLowerCase().includes(filterValue));
    }else{
      return [];
    }
  }
  showPlantSelectClearOption(){
    let list = this.getSelectedLimitList();
    return (list[0]==='Plant' || (list[0]==='Demand' && list[1]==='Plant'))?false:true;
  }

  showScrapSelectClearOption(){
    let list = this.getSelectedLimitList();
    return (list[0]==='Scrap')?false:true;
  }

  selectAlloy(alloy: string,type:string) {
    if(type==SamScenrioTypes.Scrap){
      if (!this.selectedScrapAlloys.includes(alloy)) {
        this.selectedScrapAlloys.push(alloy);
      }else{
        this.selectedScrapAlloys = this.selectedScrapAlloys.filter((scrap:string)=>scrap !=alloy)
      }
    } else if(type==SamScenrioTypes.Demand){
      if (!this.selectedDemandAlloys.includes(alloy)) {
        this.selectedDemandAlloys.push(alloy);
      }else{
        this.selectedDemandAlloys = this.selectedDemandAlloys.filter((demand:string)=>demand !=alloy)
      }
    } else if(type==SamScenrioTypes.Plant){
      let list = this.getSelectedLimitList();
      if(list[0]==='Plant' || (list[0]==='Demand' && list[1]==='Plant')){
        this.limitSelectedPlants = [alloy]
        this.filteredLimitScrapAlloys = this.limitScrapSearchControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterLimitsListAlloys(value || '',SamScenrioTypes.Scrap))
        );

      }else{
        if (!this.limitSelectedPlants.includes(alloy)) {
          this.limitSelectedPlants.push(alloy);
        }else{
          this.limitSelectedPlants = this.limitSelectedPlants.filter((plant:string)=>plant !=alloy)
        }
      }
    } else if(type==SamScenrioTypes.LimitScrap){
      let list = this.getSelectedLimitList();
      if(list[0]==='Scrap'){
        this.limitSelectedScraps = [alloy]
        this.limtitFilteredPlants = this.limitPlantSearchControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterLimitsListAlloys(value || '', SamScenrioTypes.Plant))
        );

      }else{
        if (!this.limitSelectedScraps.includes(alloy)) {
          this.limitSelectedScraps.push(alloy);
        }else{
          this.limitSelectedScraps = this.limitSelectedScraps.filter((scrap:string)=>scrap !=alloy)
        }
      }
      
    } else if(type==SamScenrioTypes.LimitDemand){
      if (!this.limitSelectedDemands.includes(alloy)) {
        this.limitSelectedDemands.push(alloy);
      }else{
        this.limitSelectedDemands = this.limitSelectedDemands.filter((scrap:string)=>scrap !=alloy)
      }
    }
  }

  generateCombinations(plants: string[], scraps: string[], demands: string[]) {
    const combinations: { Plant: string; Scrap: string; Demand: string }[] = [];
    
    plants.forEach((plant) => {
      scraps.forEach((scrap) => {
        demands.forEach((demand) => {
          combinations.push({ Plant: plant, Scrap: scrap, Demand: demand });
        });
      });
    });
  
    return combinations;
  }

  extractScrapData(obj:any,type:string){   
    let base_path = this.scrapAllFiles.filter((file:any)=>file._id==this.selectedFile)[0].dataset_location[0].path; 
    let inputData:any = {
      baseline_file:base_path,
      alloys:[],
      file_path:''
    }
    if(type==SamScenrioTypes.Scrap){
      const missingAlloys = this.selectedScrapAlloys.filter(alloy => !Object.keys(this.scrapsList).includes(alloy));
      inputData.alloys = missingAlloys;
      inputData.file_path = this.scrapFilePath;
    }else if(type==SamScenrioTypes.Demand){
      const missingAlloys = this.selectedDemandAlloys.filter(alloy => !Object.keys(this.demandsList).includes(alloy));
      inputData.alloys = missingAlloys;
      inputData.file_path = this.demandFilePath;
    }
    if(inputData.alloys.length>0){
      this.scrapAnalysisService
      .getFormatScrapDetailData(inputData)
      .then((response) => {
        if (response) {
          if(type==SamScenrioTypes.Scrap){
            this.scrapsList = Object.assign({}, this.scrapsList, response.extracted_data);
            this.addScrapScenario(obj)
          }else if(type==SamScenrioTypes.Demand){
            this.demandsList = Object.assign({}, this.demandsList, response.extracted_data);
            this.addDemandScenario(obj)
          }
        } 
      })
      .catch((error) => {
        console.error('Failed to get files:', error);
      });
  
    }else{
      if(type==SamScenrioTypes.Scrap){
        this.addScrapScenario(obj)
      }else if(type==SamScenrioTypes.Demand){
        this.addDemandScenario(obj)
      }
    }
  }
  
  addScrap(obj:any){
    this.extractScrapData(obj,SamScenrioTypes.Scrap);
  }
  addScrapScenario(obj:any){
    let index = this.scenarios.findIndex(scenario => scenario.scenario_name === obj.scenario_name)
    if (index !== -1) {
      if(this.selectedScrapAlloys.length>0){
        for(let n=0;n<this.selectedScrapAlloys.length;n++){
          if(this.scrapsList[this.selectedScrapAlloys[n]]){
            let subArray = Object.keys(this.scrapsList[this.selectedScrapAlloys[n]])
            for(let m=0;m<subArray.length;m++){
              let scrap:any = {
                Cost:0
              }
              let scrapToBeAdded = this.scrapsList[this.selectedScrapAlloys[n]][subArray[m]]
              for(let i=0;i<this.scrapColumns.length;i++){
                if(this.scrapColumns[i] !=='Cost' && this.scrapColumns[i] !=='actions'){
                  if(this.scrapColumns[i] !=='Source' && this.scrapColumns[i] !=='Alloy'){
                    scrap[this.scrapColumns[i]] = scrapToBeAdded[this.scrapColumns[i]]
                  }
                }
              }
              scrap['Alloy'] = this.selectedScrapAlloys[n]
              scrap['Source'] = subArray[m]
  
              scrap['Available Weight'] = scrapToBeAdded['Available Weight'];
              this.scenarios[index].scraps.push(scrap);  
            }

            // let scrap:any = {
            //   Cost:0
            // }
            // let scrapToBeAdded = this.scrapsList[this.selectedScrapAlloys[n]][subArray[0]]
            // for(let i=0;i<this.scrapColumns.length;i++){
            //   if(this.scrapColumns[i] !=='Cost' && this.scrapColumns[i] !=='actions'){
            //     if(this.scrapColumns[i] !=='Source' && this.scrapColumns[i] !=='Alloy'){
            //       scrap[this.scrapColumns[i]] = scrapToBeAdded[this.scrapColumns[i]]
            //     }
            //   }
            // }
            // scrap['Alloy'] = this.selectedScrapAlloys[n]
            // scrap['Source'] = (subArray.length==1)?subArray[0]:[]
            // if((subArray.length>1)){
            //   scrap['new'] = true;
            //   scrap['Available Weight'] = 0
            //   for(let j=0;j<subArray.length;j++){
            //     let scrapToBeAdded = this.scrapsList[this.selectedScrapAlloys[n]][subArray[j]];
            //     scrap['Available Weight'] = scrap['Available Weight'] + scrapToBeAdded['Available Weight'];
            //   }
            // }
            // this.scenarios[index].scraps.push(scrap);  
          }else{
            let scrap:any = {
              Cost:0
            }
              for(let i=0;i<this.scrapColumns.length;i++){
                if(this.scrapColumns[i] !=='Cost' && this.scrapColumns[i] !=='actions'){
                  if(this.scrapColumns[i] !=='Source' && this.scrapColumns[i] !=='Alloy'){
                    scrap[this.scrapColumns[i]] = 0
                  }
                }
              }
              scrap['Alloy'] = this.selectedScrapAlloys[n]
              scrap['Source'] = []
              scrap['new'] = true;          
              this.scenarios[index].scraps.push(scrap);
              this.addNewlyAddedAlloys() 
              // this.changeMade = true;
          }
        }  
      }else{
        let scrap:any = {
          Cost:0
        }
          for(let i=0;i<this.scrapColumns.length;i++){
            if(this.scrapColumns[i] !=='Cost' && this.scrapColumns[i] !=='actions'){
              if(this.scrapColumns[i] !=='Source' && this.scrapColumns[i] !=='Alloy'){
                scrap[this.scrapColumns[i]] = 0
              }
            }
          }
          scrap['Alloy'] = this.searchScrapControl.value
          scrap['Source'] = []
          scrap['new'] = true;          
          this.scenarios[index].scraps.push(scrap);  
          this.scraps.push(this.searchScrapControl.value);
          this.addNewlyAddedAlloys()
          // this.changeMade = true;
      }
      
      this.clearSeletedScrapsAll()
    }
  }
  addDemandScenario(obj:any){
    let index = this.scenarios.findIndex(scenario => scenario.scenario_name === obj.scenario_name)
    if (index !== -1) {
      if(this.selectedDemandAlloys.length>0){
        for(let n=0;n<this.selectedDemandAlloys.length;n++){
          if(this.demandsList[this.selectedDemandAlloys[n]]){
            let subArray = Object.keys(this.demandsList[this.selectedDemandAlloys[n]])
            for(let m=0;m<subArray.length;m++){
              let demand:any = {
                Cost:0
              }
              
              let scrapToBeAdded = this.demandsList[this.selectedDemandAlloys[n]][subArray[m]]
              for(let i=0;i<this.demandColumns.length;i++){
                if(this.demandColumns[i] !=='actions'){
                  if(this.demandColumns[i] !=='Plant' && this.demandColumns[i] !=='Alloy'){
                    demand[this.demandColumns[i]] = scrapToBeAdded[this.demandColumns[i]]
                  }
                }
              }
              demand['Alloy'] = this.selectedDemandAlloys[n]
              demand['Plant'] = subArray[m]
              this.scenarios[index].demands.push(demand); 
            }
            this.addNewlyAddedAlloys() 
            // let demand:any = {
            //   Cost:0
            // }
            
            // let scrapToBeAdded = this.demandsList[this.selectedDemandAlloys[n]][subArray[0]]
            // for(let i=0;i<this.demandColumns.length;i++){
            //   if(this.demandColumns[i] !=='actions'){
            //     if(this.demandColumns[i] !=='Plant' && this.demandColumns[i] !=='Alloy'){
            //       demand[this.demandColumns[i]] = scrapToBeAdded[this.demandColumns[i]]
            //     }
            //   }
            // }
            // demand['Alloy'] = this.selectedDemandAlloys[n]
            // demand['Plant'] = (subArray.length==1)?subArray[0]:[]
            // if((subArray.length>1)){
            //   demand['new'] = true;
            //   demand['Supply'] = 0;
            //   for(let j=0;j<subArray.length;j++){
            //     let demandToBeAdded = this.demandsList[this.selectedDemandAlloys[n]][subArray[j]]
            //     demand['Supply'] = demand['Supply'] + demandToBeAdded['Supply'];
            //   }
            // }
           
            // this.scenarios[index].demands.push(demand);             
          }else{
            let demand:any = {}
            for(let i=0;i<this.demandColumns.length;i++){
              if(this.demandColumns[i] !=='actions'){
                if(this.demandColumns[i] !=='Plant' && this.demandColumns[i] !=='Alloy'){
                  demand[this.demandColumns[i]] = 0
                }
              }
            }
            demand['Alloy'] = this.selectedDemandAlloys[n]
            let plants = this.getAlloyFurnace(this.selectedDemandAlloys[n])
            demand['Plant'] = (plants.length==1)?plants[0]:[]
            if(plants.length != 1){
              demand['new'] = true;
            }
            if(plants.length==1){
              if(this.limitsData.demands.indexOf(this.selectedDemandAlloys[n]) ==-1){
                this.limitsData.demands.push(this.selectedDemandAlloys[n])
              }
            }
            this.scenarios[index].demands.push(demand);  
            this.demands.push(this.searchDemandControl.value);
            this.addNewlyAddedAlloys()
            // this.changeMade = true;
          }
        }  
      }else{
        let demand:any = {}
          for(let i=0;i<this.demandColumns.length;i++){
            if(this.demandColumns[i] !=='actions'){
              if(this.demandColumns[i] !=='Plant' && this.demandColumns[i] !=='Alloy'){
                demand[this.demandColumns[i]] = 0
              }
            }
          }
          demand['Alloy'] = this.searchDemandControl.value;
          let plants = this.getAlloyFurnace(demand['Alloy'])
          demand['Plant'] = (plants.length==1)?plants[0]:[]
          // demand['Plant'] = [];
          if(plants.length != 1){
            demand['new'] = true;
          }       
          this.scenarios[index].demands.push(demand);  
          this.demands.push(this.searchDemandControl.value);
          this.addNewlyAddedAlloys()
          // this.changeMade = true;
      }
      this.clearSeletedDemandsAll()
    }
  }
  addDemand(obj:any){
    this.extractScrapData(obj,SamScenrioTypes.Demand);
  }

  clearSeletedScrapsAll() {
    this.selectedScrapAlloys = []; // Clear the selectedAlloys array
    this.searchScrapControl.setValue(''); // Reset the search input
  }

  clearSeletedDemandAll() {
    this.selectedDemandAlloys = []; // Clear the selectedAlloys array
    this.searchDemandControl.setValue(''); // Reset the search input
  }

  getAlloySources(alloy:string){
    if(this.scrapsList[alloy]){
      return Object.keys(this.scrapsList[alloy])
    }else{
      return this.allUniqueSources;
    }
  }

  getAlloyFurnace(alloy:string){
    if(this.demandsList[alloy] !== undefined){
      return Object.keys(this.demandsList[alloy])
    }else{
      return this.allUniqueFurnace;
    }
  }

  isAvailableSource(alloy:string){
    return (this.scrapsList[alloy])?true:false
  }
  
  convertSavedInfoToDisplayFormat(transformedData:any){
    const transformedData2 = transformedData.map((scenario:any) => ({
      ...scenario,
      scraps: this.convertToObjectArray(scenario.scraps),
      demands: this.convertToObjectArray(scenario.demands),
      limits: this.convertToObjectArray(scenario.limits),
    }));
  }

  convertToObjectArray(arr:any) {
    if (arr.length === 0) return [];
    const headers = arr[0]; // Get the header row (first row)
    return arr.slice(1).map((row:any) => {
      const obj: { [key: string]: any } = {};
      row.forEach((value:any, index:number) => {
        obj[headers[index]] = value;
      });
      return obj;
    });
  }

  disableActionButton(){
    if(this.usecase_id == ''){
      return (this.scenarios.length>0)?false:true;
    }else{
      return this.changeMade?false:true;
    }    
  }

  disableRunScenActionButton(){    
    return (this.scenarios.length>0 && this.usecase_id !='' && this.enableRunScenarioButton)?false:true;
  }

  disableRunViewActionButton(){
    if (this.runScenario) return true;
    if (this.usecase_id === '') return true;
    
    const viewRuns = this.scenarios.filter(scenario => scenario.results?.excel_result?.trim());
    return viewRuns.length === 0;
  }

  checkIsSelected(alloy:string){
    return this.selectedScrapAlloys.includes(alloy)
  }
  disableAddScrap(){
    return (this.selectedScrapAlloys.length==0 && this.searchScrapControl.value =='')?true:false
  }
  disableAddDemand(){
    return (this.selectedDemandAlloys.length==0 && this.searchDemandControl.value =='')?true:false
  }

  addSourceToList(element:any,obj:any){
    let index = this.scenarios.findIndex(scenario => scenario.scenario_name === obj.scenario_name);
    let ind  = this.scenarios[index].scraps.findIndex((item:any) => JSON.stringify(item) === JSON.stringify(element))
    if (index !== -1) {
      if(this.scraps.includes(element.Alloy)){
        this.scenarios[index].scraps.splice(ind,1)
        for(let i=0;i<element.Source.length;i++){
          let scrap:any = {
            Cost:0
          }
          scrap['Alloy'] = element.Alloy
          scrap['Source'] = element.Source[i]
          let listed = this.limitsData.limits.filter((limit:any)=>(limit.Alloy == element.Alloy && limit.Plant == element.Source[i]));
          if(listed.length==0){
            this.limitsData.limits.push({Alloy:element.Alloy,Plant:element.Source[i]})
          }

          if(this.scrapsList[element.Alloy]){
            let scrapToBeAdded = this.scrapsList[element.Alloy][element.Source[i]]
            for(let i=0;i<this.scrapColumns.length;i++){
              if(this.scrapColumns[i] !=='Cost' && this.scrapColumns[i] !=='actions'){
                if(this.scrapColumns[i] !=='Source' && this.scrapColumns[i] !=='Alloy'){
                  scrap[this.scrapColumns[i]] = scrapToBeAdded[this.scrapColumns[i]]
                }
              }
            }  
          }else{
            for(let i=0;i<this.scrapColumns.length;i++){
              if(this.scrapColumns[i] !=='Cost' && this.scrapColumns[i] !=='actions'){
                if(this.scrapColumns[i] !=='Source' && this.scrapColumns[i] !=='Alloy'){
                  scrap[this.scrapColumns[i]] = element[this.scrapColumns[i]]
                  // scrap[this.scrapColumns[i]] = 0
                }
              }
            }  
          }
          this.scenarios[index].scraps.push(scrap);
        }
        // this.changeMade = true;
      }
    }
  }

  addFurnaceToList(element:any,obj:any){
    let index = this.scenarios.findIndex(scenario => scenario.scenario_name === obj.scenario_name);
    let ind  = this.scenarios[index].demands.findIndex((item:any) => JSON.stringify(item) === JSON.stringify(element))
    if (index !== -1) {
      if(this.demands.includes(element.Alloy)){
        this.scenarios[index].demands.splice(ind,1)
        for(let i=0;i<element.Plant.length;i++){
          let demand:any = {}
          demand['Alloy'] = element.Alloy
          demand['Plant'] = element.Plant[i]

          if(this.limitsData.demands.indexOf(element.Alloy) ==-1){
            this.limitsData.demands.push(element.Alloy)
          }
          if(this.demandsList[element.Alloy]){
            let scrapToBeAdded = this.demandsList[element.Alloy][element.Plant[i]]
            for(let i=0;i<this.demandColumns.length;i++){
              if(this.demandColumns[i] !=='actions'){
                if(this.demandColumns[i] !=='Plant' && this.demandColumns[i] !=='Alloy'){
                  demand[this.demandColumns[i]] = scrapToBeAdded[this.demandColumns[i]]
                }
              }
            }  
          }else{
            for(let i=0;i<this.demandColumns.length;i++){
              if(this.demandColumns[i] !=='actions'){
                if(this.demandColumns[i] !=='Plant' && this.demandColumns[i] !=='Alloy'){
                  demand[this.demandColumns[i]] = 0;
                }
              }
            }
          }
          this.scenarios[index].demands.push(demand);
        }
        // this.changeMade = true;
      }
    }
  }

  getSource(scenario: any, type: string) {
    if(type=='limit'){
      if(scenario.limit_by && scenario.limit_by !='NONE'){
        let selLimitColumns = this.limitsOptions.filter((limit:any)=>limit.value==scenario.limit_by)[0].list
        this.limitColumns = selLimitColumns.concat(['actions'])
      }
    }
    let data:any = { scrap: scenario.scraps, demand: scenario.demands, limit: scenario.limits };
    return new MatTableDataSource(data[type] || []);
  }
  showEmptyResult(){
    return new MatTableDataSource([]);
  }

  deleteEntry(obj: any, type: string, entry:any){    
    const targetArray = this.typeMap[type];
    if (targetArray) {
      const updatedArray = obj[targetArray].filter((data: any) => JSON.stringify(data) !== JSON.stringify(entry));
      const index = this.scenarios.findIndex(scenario => scenario.scenario_name === obj.scenario_name);
      if (index !== -1) {        
        this.scenarios[index][targetArray] = updatedArray; // Update the array in the scenario
        this.deleteEntryFromList(entry.Alloy,type)
      }
    } else {
      console.error(`Invalid type: ${type}`);
    }
  }

  deleteEntryFromList(alloy:string,type:string){
    if(type == 'scrap'){
      let list = this.scenarios
        .map((scenario: any) => 
          scenario.scraps.filter((scrap:any)=>scrap.Alloy===alloy).map((scrap: any) => scrap.Alloy)  
        )
        .flat()  
        .filter((value, index, self) => 
          self.findIndex((v) => v === value) === index  // Ensure uniqueness by checking the plant value
        );
      if(list.length==0){
        // this.scraps = this.scraps.filter(item => item !== alloy);
        this.filteredScrapAlloys = this.searchScrapControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterListAlloys(value || '',SamScenrioTypes.Scrap))
        );

        
      }518
    }else if(type == 'demand'){
      let list = this.scenarios
      .map((scenario: any) => 
        scenario.demands.filter((demand:any)=>demand.Alloy==alloy).map((demand: any) => demand.Alloy)  
      )
      .flat()  
      .filter((value, index, self) => 
        self.findIndex((v) => v === value) === index  // Ensure uniqueness by checking the plant value
      );
      if(list.length==0){
        // this.demands = this.demands.filter(item => item !== alloy);
        this.filteredDemandAlloys = this.searchDemandControl.valueChanges.pipe(
          startWith(''),
          map(value => this.filterListAlloys(value || '',SamScenrioTypes.Demand))
        );
      }
    }
  }

  clearSeletedDemandsAll() {
    this.selectedDemandAlloys = []; // Clear the selectedAlloys array
    this.searchDemandControl.setValue(''); // Reset the search input
  }

  disableLimitButton(){
    return (this.limitSelectedPlants.length==0 || this.limitSelectedScraps.length==0 || this.limitSelectedDemands.length==0)?true:false;
  }
  addLimit(obj:any){
    if(this.limitSelectedPlants.length>0 && this.limitSelectedScraps.length>0 && this.limitSelectedDemands.length>0){
      let index = this.scenarios.findIndex(scenario => scenario.scenario_name === obj.scenario_name)
      const result = this.generateCombinations(this.limitSelectedPlants, this.limitSelectedScraps, this.limitSelectedDemands);
      if (this.scenarios[index].limits.length === 0) {
        this.scenarios[index].limits = result;
        this.scenarios[index].limits.forEach((element:any)=>{
          let index = this.limitsData.limits.findIndex((limit:any)=>limit.Plant==element.Plant && limit.Alloy == element.Scrap)
          if(index !=-1){
            if(this.limitsData.limits[index][element.Demand]){
              element['Limit'] = this.limitsData.limits[index][element.Demand];
            }
          }
        })
        // this.changeMade = true;
        this.clearSeletedLimits();
      } else {
        const existingLimits = new Set(
          this.scenarios[index].limits.map(
            (item:any) => `${item.Plant}-${item.Scrap}-${item.Demand}`
          )
        );
        // Add only new unique combinations
        const uniqueResult = result.filter(
          (item) => !existingLimits.has(`${item.Plant}-${item.Scrap}-${item.Demand}`)
        );
        if(uniqueResult.length==0){
          this.toaster.info('Already exists in limits')
          return;
        }else{
          uniqueResult.forEach((element:any)=>{
            let index = this.limitsData.limits.findIndex((limit:any)=>limit.Plant==element.Plant && limit.Alloy == element.Scrap)
            if(index !=-1){
              if(this.limitsData.limits[index][element.Demand]){
                element['Limit'] = this.limitsData.limits[index][element.Demand];
              }
            }
          })
          this.scenarios[index].limits = [
            ...this.scenarios[index].limits,
            ...uniqueResult,
          ];
          // this.changeMade = true;
          this.clearSeletedLimits();
        }      
      }
      
    }else{
      this.toaster.error('Please select the Plant,Scrap and Demand')
      return;
    }
    
  }
  toggleSourceSelection(option: string,element:any): void {
    const index = element.Source.indexOf(option);
    if (index > -1) {
      // Remove if already selected
      element.Source.splice(index, 1);
    } else {
      // Add if not selected
      if(element.Source ==''){
        element.Source = [];
      }
      element.Source.push(option);
    }
  }
  togglePlantSelection(option: string,element:any): void {
    const index = element.Plant.indexOf(option);
    if (index > -1) {
      // Remove if already selected
      element.Plant.splice(index, 1);
    } else {
      // Add if not selected
      element.Plant.push(option);
    }
  }
  transformColumn(value:string){
    return value.charAt(0).toUpperCase() + value.slice(1);
  }
  clearSeletedLimits() {
    this.limitSelectedPlants = []; // Clear the selectedAlloys array
    this.limitPlantSearchControl.setValue(''); // Reset the search input

    this.limitSelectedDemands = []; // Clear the selectedAlloys array
    this.limitDemandSearchControl.setValue(''); // Reset the search input

    this.limitSelectedScraps = []; // Clear the selectedAlloys array
    this.limitScrapSearchControl.setValue(''); // Reset the search input
    this.limitBySelected = 'NONE';
  }

  deleteLimitsData(scenario:any){
    scenario.limits = [];
  }
  duplicateScenario(scenario:any){
    let newScenarioName = '';
    let counter = 1;
    // Check if the name already exists, and keep incrementing if necessary
    do {
      newScenarioName = `Scenario ${counter}`;
      counter++;
    } while (this.scenarios.some(scenario => scenario.scenario_name === newScenarioName));
    this.scenarios.push({
      scenario_name: `${newScenarioName}`,
      results:{},
      scraps:scenario.scraps,
      demands:scenario.demands,
      limits:scenario.limits,
      limit_by:'NONE'
    })
    this.expandedAccrodian = (this.scenarios.length - 1);
    this.limitBySelected = 'NONE';
  }
  addNewscenario(){
    let newScenarioName = '';
    let counter = 1;
    // Check if the name already exists, and keep incrementing if necessary
    do {
      newScenarioName = `Scenario ${counter}`;
      counter++;
    } while (this.scenarios.some(scenario => scenario.scenario_name === newScenarioName));
    this.scenarios.push({
      scenario_name: `${newScenarioName}`,
      results:{},
      scraps:[],
      demands:[],
      limits:[],
      limit_by:'NONE'
    })
    this.expandedAccrodian = (this.scenarios.length - 1);
    this.limitBySelected = 'NONE';
    this.clearSeletedLimits();
  }

  deleteScenario(data:any){
    // this.changeMade = true;
    this.scenarios = this.scenarios.filter(scenario => scenario.scenario_name !== data.scenario_name);
  }

  toggleUsecCaseName(type:string) {
    if(type=='edit'){
      this.edit_case_name = this.use_case_name;
      this.editUsecCaseName = true;
    }else if(type=='cancel'){
      this.editUsecCaseName = false;
      this.edit_case_name = '';
    } else if(type=='done'){
      // need to call the API
      this.editUsecCaseName = false;
      // this.changeMade = true;
      this.use_case_name = this.edit_case_name;
      this.edit_case_name = '';
    }
  }

  toggleScenarioName(type:string,scenario:any){
    if(type=='edit'){
      this.editScenarioName = true;
      this.editScenarioOriginalName = scenario.scenario_name;
      this.editScenarioNewName = scenario.scenario_name;
    }else if(type=='cancel'){
      this.editScenarioName = false;
      this.editScenarioOriginalName = '';
      this.editScenarioNewName = '';
    } else if(type=='done'){
      // need to call the API
      let index = this.scenarios.findIndex((scen:any)=>scen.scenario_name == this.editScenarioNewName);
      if(index != -1){
        this.toaster.error('Scenario name already exists', '', {
          positionClass: 'custom-toast-position',
        });
        return;  
      }else{
        scenario.scenario_name = this.editScenarioNewName;
        this.editScenarioName = false;
        this.editScenarioOriginalName = '';
        this.editScenarioNewName = '';
        // this.changeMade = true;
      }      
    }
  
  }
  columnNotVisualizAndFurnace(column:string){
    return (column != 'Plant' && column !='Alloy')?true:false;
  }
  columnNameMap(column:string){
    if(column == 'Plant'){
      return 'Furnace'
    }else if(column == 'Supply' || column == 'Available Weight'){
      return 'Available'
    }else{
      return column
    }
  }
  saveScenarioText(){
    return (this.usecase_id !='')?'Update Scenarios':'Save Scenarios';
  }
  updateExistingUsecaseData(){
    this.usecase_id = this.useCaseDetail.usecase_id;
    this.use_case_name = this.useCaseDetail.usecase_name;
    this.selectedFile = this.useCaseDetail.baseline_file;
    this.selectedToDisplayFile = this.useCaseDetail.baseline_file;
    this.use_case_description = this.useCaseDetail.usecase_desc;
    this.scenarios = this.convertDbObjectToReadable(this.useCaseDetail);
    this.setSourcePlantUpdate()
  }

  saveScenarios(){
    if(!this.changeMade && this.usecase_id !=''){
      return;
    }

    if(this.selectedFile == ''){
      this.toaster.error('Please select baseline file', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }

    if(this.use_case_name == ''){
      this.toaster.error('Please enter usecase name', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }

    let objToSave:any = {
      "baseline_file": this.selectedToDisplayFile,
      "usecase_name": this.use_case_name,
      "usecase_desc": this.use_case_description,
      "config_content": '',
      "scenarios": this.transformScenariosData(this.scenarios),
      "user_id": this.currentUser._id
    }

    if(this.usecase_id !=''){
      objToSave.usecase_id = this.usecase_id;
      objToSave.created_date = this.useCaseDetail.created_date;
    }

    this.scrapAnalysisService
    .saveUsecaseData(objToSave)
    .then((response:any) => {
      if (response) {
        if(response['usecase_id'] && response['usecase_id'] !=''){
          this.toaster.success(response['message'], '', {
            positionClass: 'custom-toast-position',
          });
          this.savedResponse = response.usecase_data;
          this.useCaseDetail = this.savedResponse
          this.limitBySelected = 'NONE';
          this.usecase_id = response['usecase_id']
          this.updateExistingUsecaseData();
          this.changeMade = false;
          this.enableRunScenarioButton = true;
          let index = this.useCasesList.findIndex((usecase:any)=>usecase.usecase_id==this.usecase_id)
          if(index !=-1){
            this.useCasesList[index] = response.usecase_data
          }else{
            this.useCasesList.push(response.usecase_data)
          }
          this.useCaseEvent.emit(this.useCasesList);
        }else{
          this.toaster.error(response['message'], '', {
            positionClass: 'custom-toast-position',
          });
        }
        
      } else{
        this.toaster.error('Failed to save scenario', '', {
          positionClass: 'custom-toast-position',
        });
      }
    })
    .catch((error) => {
      console.error('Failed to get files:', error);
      this.toaster.error('Failed to save scenario', error, {
        positionClass: 'custom-toast-position',
      });
    });
  }

  transformScenariosData(originalData: any) {
    let limitColumns: string[] = [
      'Plant',
      'Scrap',
      'Demand',
      'Limit',
      'actions'
    ];
    return originalData.map((scenario:any) => {
      const transformedScenario = {
        scenario_name: scenario.scenario_name,
        results:(scenario.results)?scenario.results:{},
        scraps: this.getTransformedData(scenario.scraps,this.scrapColumns),
        demands: this.getTransformedData(scenario.demands,this.demandColumns),
        limits: this.getTransformedData(scenario.limits,limitColumns),
        limit_by: (scenario.limit_by)?scenario.limit_by:'NONE'
      };
      return transformedScenario;
    });
  }

  getTransformedData(data: any, columns: string[]): any {
    let transformed: any = {};    
    for (let i = 0; i < columns.length; i++) {
      if (columns[i] !== 'actions') {
        // Check if the column is 'Source' and the array is empty
        if (columns[i] === 'Source' || columns[i] === 'Plant') {
          transformed[columns[i]] = data.map((item: any) =>             
            Array.isArray(item[columns[i]]) || item[columns[i]].length === 0 ? '' : item[columns[i]]
          );
        } else {
          transformed[columns[i]] = data.map((item: any) => item[columns[i]]);
        }
      }
    } 
    return transformed;
  }
  executeScenarios(){
    this.runScenario = true;
    this.scrapAnalysisService
      .runUsecasScenarios(this.usecase_id,this.currentUser._id)
      .then((runresponse) => {
         this.runScenario = false;
            if (runresponse) {
              if(runresponse['usecase_id'] && runresponse['usecase_id'] !=''){
                this.toaster.success('Scenario run successfully', '', {
                  positionClass: 'custom-toast-position',
                });           
                this.savedResponse = runresponse;
                this.savedResponse.usecase_id = runresponse['usecase_id']
                this.useCaseDetail = this.savedResponse
                this.usecase_id = runresponse['usecase_id']
                this.updateExistingUsecaseData();
                this.enableRunScenarioButton = false;
                
                let index = this.useCasesList.findIndex((usecase:any)=>usecase.usecase_id==this.usecase_id)
                if(index !=-1){
                  this.useCasesList[index] = this.savedResponse
                }else{
                  this.useCasesList.push(this.savedResponse)
                }
                this.useCaseEvent.emit(this.useCasesList);
              }else{
                this.toaster.error('Failed to run scenarios', '', {
                  positionClass: 'custom-toast-position',
                });
              }              
            } else{
              this.runScenario = false;
              this.toaster.error('Failed to run scenarios', '', {
                positionClass: 'custom-toast-position',
              });
            }   
      })
      .catch((error) => {
        this.runScenario = false;
        console.error('Failed to run scenarios:', error);
        this.toaster.error('Failed to run scenarios', '', {
          positionClass: 'custom-toast-position',
        });
     });      
  }
  runScenarios(){
    if(this.changeMade){
      if(this.selectedFile == ''){
        this.toaster.error('Please select baseline file', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }
      if(this.use_case_name == ''){
        this.toaster.error('Please enter usecase name', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }

      let saveData:any = {
        "baseline_file": this.selectedToDisplayFile,
        "usecase_name": this.use_case_name,
        "usecase_desc": this.use_case_description,
        "config_content": '',
        "scenarios": this.transformScenariosData(this.scenarios),
        "user_id": this.currentUser._id
      }
      if(this.usecase_id !=''){
        saveData['usecase_id'] = this.usecase_id;
        saveData['created_date'] = this.useCaseDetail.created_date;
      }
      this.scrapAnalysisService
      .saveUsecaseData(saveData)
      .then((response) => {
        if (response) {
          if(response['usecase_id'] && response['usecase_id'] !=''){

            this.savedResponse = response.usecase_data;
            this.useCaseDetail = this.savedResponse;
            this.limitBySelected = 'NONE';
            this.usecase_id = response['usecase_id'];
            this.updateExistingUsecaseData();
            this.changeMade = false;
            this.enableRunScenarioButton = true;
            let index = this.useCasesList.findIndex((usecase:any)=>usecase.usecase_id==this.usecase_id)
            if(index !=-1){
              this.useCasesList[index] = this.savedResponse
            }else{
              this.useCasesList.push(this.savedResponse)
            }
            this.useCaseEvent.emit(this.useCasesList);
            
            this.executeScenarios();
            
          }else{
            this.toaster.error(response['message'], '', {
              positionClass: 'custom-toast-position',
            });
          }
        } else{
          this.toaster.error('Failed to save scenario', '', {
            positionClass: 'custom-toast-position',
          });
        }
      })
      .catch((error) => {
        console.error('Failed to get files:', error);
        this.toaster.error('Failed to save scenario', error, {
          positionClass: 'custom-toast-position',
        });
      });
    }else{
      this.executeScenarios();
    }
    
  }
}

