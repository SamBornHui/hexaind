import { Component, Output, EventEmitter, Inject, OnInit, ViewChild, OnDestroy } from "@angular/core";
import { Project } from "src/app/models/project-models";
import { ApiService } from "src/app/services/api.service";
import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { ToastrService } from "ngx-toastr";
import { SnackBarNotificationService } from "src/app/services/snack-bar-notification.service";
import { UsersService } from "src/app/pages/users/users.service";
import { ConfigService } from '../../services/config.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { FormBuilder, FormGroup, Validators,FormControl  } from '@angular/forms';
import { NgxMaterialTimepickerComponent } from 'ngx-material-timepicker';
import { Subscription } from 'rxjs';
import { EventType } from "@angular/router";
import { FileStructureNodeResponse } from "src/app/models/api-models";
import { NestedTreeControl } from "@angular/cdk/tree";
import { MatTreeNestedDataSource } from "@angular/material/tree";
import { SelectionModel } from "@angular/cdk/collections";
import { TreeNode } from "primeng/api";
import { MatSelectChange } from '@angular/material/select';

interface EventBasedConfig {
  event_type: string;
  config: {
    folder_path?: string;
    workflow_id?: string;
    condition?: string;
    event_type: string;
    file_name?: string | null;
  };
}

interface FormattedData {
  name: string;
  workflow_id: string;
  start_date: string;
  end_date?: string;
  schedule_type: string;
  schedule_interval: string;
  tags: string[];
  event_based_config?: EventBasedConfig;
  schedule_interval_metadata: {
    name: string;
    workflow_id: string;
    schedule_type: string;
    start_datetime: string;
    workflow_name?: string;
    end_datetime?: string;
    repeatEvery?: string;
    repeatType?: string;
    weekDays?: string[];
  };
  schedule_id?: string;
  repeat_type?: string; 
  repeat_value?: number;
  cron_week_days?: number[];
}

@Component({
  selector: 'app-create-schedule',
  templateUrl: './create-schedule.component.html',
  styleUrls: ['./create-schedule.component.less'],
})
export class CreateNewScheduleComponent implements OnInit {
  @Output() closePanelClicked = new EventEmitter<any>();
  @ViewChild('datetimePicker') datetimePicker: NgxMaterialTimepickerComponent | undefined;
  addEvent: EventEmitter<any> = new EventEmitter<any>();
  formData: FormGroup = this.fb.group({});
  selectedOccurrence: string = ''; // initialize with empty string
  selectedRepeat: string = ''; // initialize with empty string
  sessions: any[] = []; 
  minDate: Date = new Date();
  private occurrenceTypeSubscription: Subscription | undefined;
  time = new FormControl();

  dataStructure: any = [];
  filteredDataStructure: any = [];
  currentFolderView: any = [];
  treeTableData!: TreeNode[];

  times: string[] = [];
  schedule_data:any;
  response: any;
  isLoading: boolean = false;

  treeControl = new NestedTreeControl<FileStructureNodeResponse>(
    (node) => node.children,
  );
  dataSource = new MatTreeNestedDataSource<FileStructureNodeResponse>();
  selection = new SelectionModel<FileStructureNodeResponse>(false);
  files: any = [];
  path: any;
  folderService: any;
  new_folder_name: string = '';
  isSubmitting = false;
  hasChild = (_: number, node: FileStructureNodeResponse) =>
    !!node.children && node.children.length > 0;
  folderPath: string | undefined;

  WEEKS: string = 'Weeks'
  enableSchedule: boolean = false
  
  constructor(
    private dialogRef: MatDialogRef<CreateNewScheduleComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any, // Inject the project data
    private apiService: ApiService,
    public toaster: ToastrService,
    private snackBarNotification: SnackBarNotificationService,
    private usersService: UsersService,
    private configService: ConfigService,
    private sessionApi: WorkflowsSessionsApiService,
    private fb: FormBuilder
  ) {

   }

  async ngOnInit(){
    this.getFoldersData();
    this.initializeForm();
    this.loadWorkflowSessions();
    this.generateTimes();

    this.formData.get('repeatEvery')?.valueChanges.subscribe(() => {
      this.resetWeekDays();
    });

    if(this.data.isEdit){ 
      let selectedProject = this.configService.SelectedProjectId;
      this.schedule_data = await this.apiService.getScheduleById('1',selectedProject,this.data.rowData);
      
      if (this.schedule_data.schedule_interval_metadata.schedule_type === 'ONCE') {
      const [onceDateTime, time, utcDate] = this.convertFromUTC(this.schedule_data.schedule_interval_metadata.start_datetime);
      // const time = this.schedule_data.schedule_interval_metadata.start_time;
      
      this.formData.patchValue({
        name: this.schedule_data.schedule_interval_metadata.name,
        workflow: this.schedule_data.schedule_interval_metadata.workflow_id,
        occurrenceType: this.schedule_data.schedule_interval_metadata.schedule_type,
        onceDateTime: onceDateTime,
        time: time
      });
    } else {
        const [startDate, startTime, utcStartDate ] = this.convertFromUTC(this.schedule_data.schedule_interval_metadata.start_datetime); 
        // const startTime = this.schedule_data.schedule_interval_metadata.start_time;
        const [endDate, endTime, utcEndDate] = this.convertFromUTC(this.schedule_data.schedule_interval_metadata.end_datetime);
        // const endTime = this.schedule_data.schedule_interval_metadata.end_time;

        if (this.schedule_data.repeat_type === this.WEEKS) {
          this.schedule_data.cron_week_days = this.schedule_data.cron_week_days.map(
            (dayId: number) => {
              return this.getCronDay(this.adjustWeekdayFromUTC(utcStartDate,dayId));
            }
          )
        }
        
        this.formData.patchValue({
          name: this.schedule_data.schedule_interval_metadata.name,
          workflow: this.schedule_data.schedule_interval_metadata.workflow_id,
          occurrenceType: this.schedule_data.schedule_interval_metadata.schedule_type,
          repeatEvery: this.schedule_data.schedule_interval_metadata.repeatEvery,
          repeatType: this.schedule_data.schedule_interval_metadata.repeatType,
          weekDays: this.schedule_data.cron_week_days,
          recurringStartDate: startDate,
          recurringStartTime: startTime,
          recurringEndDate: endDate,
          recurringEndTime: endTime
      });
    }
    if (this.schedule_data.event_based_config) {
      this.formData.patchValue({
        eventBasedConfig: true,
        eventType: this.schedule_data.event_based_config.event_type,
        workflowId: this.schedule_data.event_based_config.config.workflow_id,
        folderPath: this.schedule_data.event_based_config.config.folder_path
      });
    }
    }else{ 
      if(this.data.workflow_id != ''){
      this.formData.patchValue({
        workflow: this.data.workflow_id
      });
      }
    }
  }
  
  convertFromUTC = (utcDateTime: string) : [Date,string,Date] => {
      const [datePart, timePart] = utcDateTime.split(' ');
      const [year, month, day] = datePart.split('-').map(Number);
      const [hours, minutes, seconds] = timePart.split(':').map(Number);

      const utcDate = new Date(Date.UTC(year, month - 1, day, hours, minutes, seconds));
      
      const localYear = utcDate.getFullYear();
      const localMonth = ('0' + (utcDate.getMonth() + 1)).slice(-2);  
      const localDay = ('0' + utcDate.getDate()).slice(-2);
      const localHours = ('0' + utcDate.getHours()).slice(-2);
      const localMinutes = ('0' + utcDate.getMinutes()).slice(-2);

      const date = `${localYear}-${localMonth}-${localDay}`;
      const time = `${localHours}:${localMinutes}`;
      
      return [new Date(`${date}T00:00:00`),time,utcDate];
  };

  adjustWeekdayFromUTC = (utcDate: Date, dayId: number) => {
    const utcDay = utcDate.getUTCDay();
    const localDay = utcDate.getDay();  
    
    const diff = localDay - utcDay;
    const adjustedDayId = (dayId + diff + 7) % 7;  
    return adjustedDayId;
  };

  onWeekDaySelection(event: any) { 
    const repeatEvery = this.formData.get('repeatEvery')?.value;
    
    // Check if 'Repeat Every' is 2 or 3 and 'Repeat Type' is 'Weeks'
    if (this.formData.get('repeatType')?.value === 'Weeks' && (repeatEvery === '2' || repeatEvery === '3' || repeatEvery === '4' || repeatEvery === '5' || repeatEvery === '6')) { 
      const selectedDays = event.value;
      
      // If more than one day is selected, uncheck the previous selection
      if (selectedDays.length > 1) {
        this.formData.get('weekDays')?.setValue([selectedDays[1]]);
      }
    } 
  }

  resetWeekDays() {
    const weekDaysControl = this.formData.get('weekDays');
    if (weekDaysControl) {
      weekDaysControl.reset(); // Clear the selected week days
    }
  }
  

  getFoldersData() {
    this.apiService
      .getFolderStructureList('')
      .then((response) => { 
        if (response) {
          this.dataStructure = response;
          this.currentFolderView = response;
          this.filteredDataStructure = [...this.dataStructure];
          this.treeTableData = this.convertData(this.filteredDataStructure);
          this.files = this.filterFolderNode(this.dataStructure);
          this.dataSource.data = this.files;
          this.treeControl.dataNodes = this.dataSource.data;
          this.treeControl.expandAll();
        } else {
          this.dataStructure = [];
          this.filteredDataStructure = [];
        }
      })
      .catch((error) => {
        console.error('Error fetching mounted drive data:', error);
      });
  }

  filterFolderNode(
    nodes: FileStructureNodeResponse[],
    isRoot: boolean = true
  ): FileStructureNodeResponse[] {
    const filteredNodes: FileStructureNodeResponse[] = [];
  
    nodes.forEach((node: FileStructureNodeResponse) => {
      if (node.type === 'folder') {
        // Recursively include all children (folders and files)
        const children = node.children
          ? node.children // Directly use node.children without filtering
          : [];
        // Include folder nodes with their children
        const newNode = { ...node, children };
        filteredNodes.push(newNode);
      } else if (node.type === 'file' && !isRoot) {
        // Include files only if they are not in the root level
        filteredNodes.push(node);
      }
    });
  
    return filteredNodes;
  }
  
  
  filterTreeNode(
    nodes: FileStructureNodeResponse[],
    filterText: string,
  ): FileStructureNodeResponse[] {
    const filteredNodes: FileStructureNodeResponse[] = [];
    nodes.forEach((node: any) => {
      const children = node.children
        ? this.filterTreeNode(node.children, filterText)
        : [];

      if (
        node.name.toLowerCase().includes(filterText.toLowerCase()) ||
        children.length > 0
      ) {
        const newNode = { ...node, children };
        filteredNodes.push(newNode);
      }
    });

    return filteredNodes;
  }

  convertData(data: any): any { 
    return data.map((item: any) => {
      const convertedItem: any = {
        data: {
          name: item.name,
          size: item.size ? item.size : '',
          type: item.type,
          last_modified_at: item.last_modified_at ? item.last_modified_at : '',
          full_path: item.full_path,
          _id: item._id ? item._id : '',
          project_id: item.project_id,
          parent_id: item.parent_id,
          site_id: item.site_id,
          created_by: item.created_by ? item.created_by : '',
          created_at: item.created_at ? item.created_at : '',
          dataset_type: item.dataset_type ? item.dataset_type : '',
        },
        children: [],
      };

      if (item.children && item.children.length > 0) {
        convertedItem.children = this.convertData(item.children);
      }
      return convertedItem;
    });
  }

  getSelectedSessionName(): string {
    if (this.data.workflow_id && this.sessions) {
      const selectedSession = this.sessions.find(session => session._id === this.data.workflow_id);
      return selectedSession ? selectedSession.name : '';
    }
    return '';
  }
  

  ngOnDestroy(): void {
    if (this.occurrenceTypeSubscription) {
      this.occurrenceTypeSubscription.unsubscribe();
    }
  }

  generateTimes() {
    for (let hour = 0; hour < 24; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        const formattedHour = ('0' + hour).slice(-2);
        const formattedMinute = ('0' + minute).slice(-2);
        this.times.push(`${formattedHour}:${formattedMinute}`);
      }
    }
  }

  initializeForm(): void {
    this.formData = this.fb.group({
      name: ['', Validators.required],
      workflow: ['', Validators.required],
      occurrenceType: ['Once', Validators.required],
      onceDateTime: [''],
      time: [''],
      repeatEvery: [''],
      repeatType: [''],
      weekDays: [[]],
      recurringStartDate: [''],
      recurringStartTime: [''],
      recurringEndDate: [''],
      recurringEndTime: [''],
      eventBasedConfig: [false],
      eventType: [''],
      workflowId: [''],
      folderPath: ['']

    });

    // Subscribe to changes in occurrenceType control
    // this.occurrenceTypeSubscription = this.formData.get('occurrenceType')?.valueChanges.subscribe((value) => {
    //   if (value === 'ONCE') { 
    //     this.clearRecurringFields();
    //   } else {
    //     this.clearOnceFields();
    //   }
    // });
  }

  clearOnceFields(): void {
    this.formData.patchValue({
      onceDateTime: '',
      time: '', 
    });
  }

  clearRecurringFields(): void {
    this.formData.patchValue({
      repeatEvery: '',
      repeatType: '',
      weekDays: [],
      recurringStartDate: '',
      recurringStartTime: '',
      recurringEndDate: '',
      recurringEndTime: ''
    });
  }

  async loadWorkflowSessions() {
    try {
      let selectedProject = this.configService.SelectedProjectId;
      if (selectedProject) {
        //this.sessions = await this.sessionApi.GetWorkflowSessions(this.configService.SelectedSiteId, selectedProject);
        this.sessions = await this.apiService.GetWorkflows(undefined);
      }
    } catch (error) {
      console.error("Error loading workflow sessions:", error);
    }
  }

  // async onSubmit() { 
  //   if (this.formData.valid) {
  //     const data = this.formData.value;
  //     const repeatEvery = data.repeatEvery;
  //     const repeatType = data.repeatType;
  //     const weekDays = data.weekDays;
  //     const cronExpression = this.generateCronExpression(repeatEvery, repeatType, weekDays);       
  
  //     let formattedData: FormattedData = {
  //       name: data.name,
  //       workflow_id: data.workflow,
  //       start_date: '',
  //       schedule_type: '',
  //       schedule_interval: '',
  //       tags: [data.workflow, data.name],
  //       schedule_interval_metadata: {
  //         name: data.name,
  //         workflow_id: data.workflow,
  //         schedule_type: '',
  //         start_date: ''
  //       }
  //     };
  
  //     if (data.occurrenceType == 'ONCE') { 
  //       const onceDateTime = new Date(data.onceDateTime);
  //       // const dateOnly = `${onceDateTime.getFullYear()}-${('0' + (onceDateTime.getMonth() + 1)).slice(-2)}-${('0' + onceDateTime.getDate()).slice(-2)}`;
  //       // const timeOnly = data.time;
  //       // const seconds = '00';

  //       const dateOnly = `${onceDateTime.getFullYear()}-${('0' + (onceDateTime.getMonth() + 1)).slice(-2)}-${('0' + onceDateTime.getDate()).slice(-2)}`;
  //       const timeOnly = data.time;
  //       const seconds = '00';

  //       // Combine date and time into a single string
  //       const localDateTimeString = `${dateOnly}T${timeOnly}:${seconds}`; // Use 'T' to separate date and time

  //       // Create a Date object from the local date and time string
  //       const localDateTime = new Date(localDateTimeString);

  //       // Convert the local date and time to UTC
  //       const year = localDateTime.getUTCFullYear();
  //       const month = ('0' + (localDateTime.getUTCMonth() + 1)).slice(-2);
  //       const day = ('0' + localDateTime.getUTCDate()).slice(-2);
  //       const hours = ('0' + localDateTime.getUTCHours()).slice(-2);
  //       const minutes = ('0' + localDateTime.getUTCMinutes()).slice(-2);
  //       const secondsUTC = ('0' + localDateTime.getUTCSeconds()).slice(-2);

  //       // Format the UTC date and time string
  //       formattedData.start_date = `${year}-${month}-${day} ${hours}:${minutes}:${secondsUTC}`;

  //       console.log(formattedData.start_date,"UTC time zone"); 
  
  //       //formattedData.start_date = `${dateOnly} ${timeOnly}:${seconds}`;
  //       formattedData.schedule_type = 'ONCE';
  //       formattedData.schedule_interval = '@once';
  //       formattedData.schedule_interval_metadata.start_date = dateOnly;
  //       formattedData.schedule_interval_metadata.start_time = timeOnly;
  //       formattedData.schedule_interval_metadata.schedule_type = 'ONCE';
  //       formattedData.schedule_interval_metadata.workflow_name = data.workflow_name;
  
  //       if (data.eventType) {
  //         if (data.eventType === 'WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF') {
  //           formattedData.event_based_config = {
  //             event_type: data.eventType,
  //             config: {
  //               workflow_id: data.workflowId,
  //               event_type: data.eventType,
  //               condition: 'SUCCEEDED'
  //             }
  //           };
  //         } else if (data.eventType === 'ANY_FILE_IN_FOLDER_TRIGGER_WF') {
  //           formattedData.event_based_config = {
  //             event_type: data.eventType,
  //             config: {
  //               folder_path: this.folderPath,
  //               event_type: data.eventType,
  //               file_name: data.fileName || null
  //             }
  //           };
  //         }
  //       }
  
  //       if (this.data.isEdit) {
  //         formattedData.schedule_id = this.data.rowData._id;
  //       }
  //       const selectedProject = this.configService.SelectedProjectId;
  //       if (this.data.isEdit) {
  //         this.response = await this.apiService.updateScheduleWorkflow('1', selectedProject, formattedData);
  //         this.handleApiResponse(this.response, 'Scheduled Updated Successfully');
  //       } else {
  //         this.response = await this.apiService.createScheduleWorkflow('1', selectedProject, formattedData);
  //         this.handleApiResponse(this.response, 'Scheduled Created Successfully');
  //       }
  //     }
  
  //     if (data.occurrenceType == 'RECURRING') {
  //       if (data.recurringStartDate !== '') {
  //         const recurringStartDate = new Date(data.recurringStartDate);
  //         const recurringEndDate = new Date(data.recurringEndDate);
  //         const startDateOnly = `${recurringStartDate.getFullYear()}-${('0' + (recurringStartDate.getMonth() + 1)).slice(-2)}-${('0' + recurringStartDate.getDate()).slice(-2)}`;
  //         const endDateOnly = `${recurringEndDate.getFullYear()}-${('0' + (recurringEndDate.getMonth() + 1)).slice(-2)}-${('0' + recurringEndDate.getDate()).slice(-2)}`;
  //         const startTimeOnly = data.recurringStartTime;
  //         const endTimeOnly = data.recurringEndTime;
  //         const startDateTime = `${startDateOnly} ${startTimeOnly}:00`;
  //         const endDateTime = `${endDateOnly} ${endTimeOnly}:00`;
  
  //         formattedData.start_date = startDateTime;
  //         formattedData.end_date = endDateTime;
  //         formattedData.schedule_type = 'RECURRING';
  //         formattedData.schedule_interval = cronExpression;
  //         formattedData.schedule_interval_metadata.start_date = startDateOnly;
  //         formattedData.schedule_interval_metadata.end_date = endDateOnly;
  //         formattedData.schedule_interval_metadata.start_time = startTimeOnly;
  //         formattedData.schedule_interval_metadata.end_time = endTimeOnly;
  //         formattedData.schedule_interval_metadata.schedule_type = 'RECURRING';
  //         formattedData.schedule_interval_metadata.repeatEvery = data.repeatEvery;
  //         formattedData.schedule_interval_metadata.repeatType = data.repeatType;
  //         formattedData.schedule_interval_metadata.weekDays = data.weekDays;
  
  //         if (data.eventType) {
  //           if (data.eventType === 'WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF') {
  //             formattedData.event_based_config = {
  //               event_type: data.eventType,
  //               config: {
  //                 workflow_id: data.workflowId,
  //                 event_type: data.eventType,
  //                 condition: 'SUCCEEDED'
  //               }
  //             };
  //           } else if (data.eventType === 'ANY_FILE_IN_FOLDER_TRIGGER_WF') {
  //             formattedData.event_based_config = {
  //               event_type: data.eventType,
  //               config: {
  //                 folder_path: this.folderPath,
  //                 event_type: data.eventType,
  //                 file_name: data.fileName || null
  //               }
  //             };
  //           }
  //         }
  
  //         if (this.data.isEdit) {
  //           formattedData.schedule_id = this.data.rowData._id;
  //         }
  
  //         const selectedProject = this.configService.SelectedProjectId;
  //         if (this.data.isEdit) {
  //           this.response = await this.apiService.updateScheduleWorkflow('1', selectedProject, formattedData);
  //           this.handleApiResponse(this.response, 'Scheduled Updated Successfully');
  //         } else {
  //           this.response = await this.apiService.createScheduleWorkflow('1', selectedProject, formattedData);
  //           this.handleApiResponse(this.response, 'Scheduled Created Successfully');
  //         }
  //       }
  //     }
  //   }
  // }

  async onSubmit() {
    if (this.isSubmitting) {
      return; // Prevent further execution if already submitting
    }

    this.isSubmitting = true;

    // Simulate form submission logic (e.g., API call)
    console.log('Form submitted:', this.formData.value);

    // Reset the flag after the operation (example: after API response)
    setTimeout(() => {
      this.isSubmitting = false;
    }, 3000); // Replace with actual logic
    if (this.formData.valid) {
      const data = this.formData.value;
      const repeatEvery = data.repeatEvery;
      const repeatType = data.repeatType;
      const weekDays = data.weekDays;
      // const cronExpression = this.generateCronExpression(repeatEvery, repeatType, weekDays);
  
      let formattedData: FormattedData = {
        name: data.name,
        workflow_id: data.workflow,
        start_date: '',
        schedule_type: '',
        schedule_interval: '',
        tags: [data.workflow, data.name],
        schedule_interval_metadata: {
          name: data.name,
          workflow_id: data.workflow,
          schedule_type: '',
          start_datetime: ''
        }
      };
  
      const convertToUTC = (localDate: Date, time: string, dayid?: number): [string, Date] => {
        const dateOnly = `${localDate.getFullYear()}-${('0' + (localDate.getMonth() + 1)).slice(-2)}-${('0' + localDate.getDate()).slice(-2)}`;
        const localDateTimeString = `${dateOnly}T${time}:00`;
        const localDateTime = new Date(localDateTimeString);
  
        const year = localDateTime.getUTCFullYear();
        const month = ('0' + (localDateTime.getUTCMonth() + 1)).slice(-2);
        const day = ('0' + localDateTime.getUTCDate()).slice(-2);
        const hours = ('0' + localDateTime.getUTCHours()).slice(-2);
        const minutes = ('0' + localDateTime.getUTCMinutes()).slice(-2);
        const seconds = ('0' + localDateTime.getUTCSeconds()).slice(-2);
  
        return [`${year}-${month}-${day} ${hours}:${minutes}:${seconds}`, localDateTime];
      };

      const adjustWeekdayToUTC = (localDate: Date, dayId: number) => {
        const diff = localDate.getUTCDay() - localDate.getDay();
        return (dayId + diff + 7) % 7;
      };
  
      if (data.occurrenceType == 'ONCE') {
        const onceDateTime = new Date(data.onceDateTime);
        const [startDateTime, localDateTime] = convertToUTC(onceDateTime, data.time);
      
        // Calculate end date by adding 1 year
        const endDateTime = new Date(onceDateTime);
        endDateTime.setFullYear(endDateTime.getFullYear() + 1);
        const [formattedEndDateTime, localEndDateTime] = convertToUTC(endDateTime, data.time); // Convert endDateTime

        formattedData.start_date = startDateTime;
        formattedData.end_date = formattedEndDateTime; // Ensure same format as start_date
      
        formattedData.start_date = startDateTime;
        formattedData.end_date = formattedEndDateTime; // Add end date
      
        formattedData.schedule_type = 'ONCE';
        formattedData.schedule_interval = '@once';
        formattedData.schedule_interval_metadata.start_datetime = startDateTime;
        formattedData.schedule_interval_metadata.end_datetime = formattedEndDateTime; // Add end datetime
        formattedData.schedule_interval_metadata.schedule_type = 'ONCE';
        formattedData.schedule_interval_metadata.workflow_name = data.workflow_name;
      
        if (data.eventType) {
          if (data.eventType === 'WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF') {
            formattedData.event_based_config = {
              event_type: data.eventType,
              config: {
                workflow_id: data.workflowId,
                event_type: data.eventType,
                condition: 'SUCCEEDED'
              }
            };
          } else if (data.eventType === 'ANY_FILE_IN_FOLDER_TRIGGER_WF') {
            formattedData.event_based_config = {
              event_type: data.eventType,
              config: {
                folder_path: this.folderPath,
                event_type: data.eventType,
                file_name: data.fileName || null
              }
            };
          }
        }
      
        if (this.data.isEdit) {
          formattedData.schedule_id = this.data.rowData._id;
        }
        
        const selectedProject = this.configService.SelectedProjectId;
        if (this.data.isEdit) {
          this.response = await this.apiService.updateScheduleWorkflow('1', selectedProject, formattedData);
          this.handleApiResponse(this.response, 'Scheduled Updated Successfully');
        } else {
          this.response = await this.apiService.createScheduleWorkflow('1', selectedProject, formattedData);
          this.handleApiResponse(this.response, 'Scheduled Created Successfully');
        }
      }
      
  
      if (data.occurrenceType == 'RECURRING') {
        if (data.recurringStartDate !== '') {
          const recurringStartDate = new Date(data.recurringStartDate);
          const recurringEndDate = new Date(data.recurringEndDate);
          const [startDateTime, localStartDateTime ]= convertToUTC(recurringStartDate, data.recurringStartTime);
          const [endDateTime, localStartEndTime] = convertToUTC(recurringEndDate, data.recurringEndTime);
  
          formattedData.start_date = startDateTime;
          formattedData.end_date = endDateTime;
          formattedData.schedule_type = 'RECURRING';
          formattedData.schedule_interval = '@recurring';
          formattedData.schedule_interval_metadata.start_datetime = startDateTime;
          formattedData.schedule_interval_metadata.end_datetime = endDateTime;
          formattedData.schedule_interval_metadata.schedule_type = 'RECURRING';
          formattedData.schedule_interval_metadata.repeatEvery = data.repeatEvery;
          formattedData.schedule_interval_metadata.repeatType = data.repeatType;
          formattedData.schedule_interval_metadata.weekDays = data.weekDays;
                  
          formattedData.repeat_type = data.repeatType;
          formattedData.repeat_value = Number(data.repeatEvery);

          if (formattedData.repeat_type === this.WEEKS && data.weekDays) {
            formattedData.cron_week_days = data.weekDays.map((day: string) => {
              const newdayid = adjustWeekdayToUTC(localStartDateTime,this.getCronDayId(day));
              return newdayid;
            });
          }
  
          if (data.eventType) {
            if (data.eventType === 'WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF') {
              formattedData.event_based_config = {
                event_type: data.eventType,
                config: {
                  workflow_id: data.workflowId,
                  event_type: data.eventType,
                  condition: 'SUCCEEDED'
                }
              };
            } else if (data.eventType === 'ANY_FILE_IN_FOLDER_TRIGGER_WF') {
              formattedData.event_based_config = {
                event_type: data.eventType,
                config: {
                  folder_path: this.folderPath,
                  event_type: data.eventType,
                  file_name: data.fileName || null
                }
              };
            }
          }
  
          if (this.data.isEdit) {
            formattedData.schedule_id = this.data.rowData._id;
          }
  
          const selectedProject = this.configService.SelectedProjectId;
          if (this.data.isEdit) {
            this.response = await this.apiService.updateScheduleWorkflow('1', selectedProject, formattedData);
            this.handleApiResponse(this.response, 'Scheduled Updated Successfully');
          } else {
            this.response = await this.apiService.createScheduleWorkflow('1', selectedProject, formattedData);
            this.handleApiResponse(this.response, 'Scheduled Created Successfully');
          }
        }
      }
    }
  }
  
  
  handleApiResponse(response: any, successMessage: string) {
    if (response.succeeded) {
      this.isLoading = true;
      this.isLoading = false;
      this.toaster.success(successMessage, '', {
        positionClass: 'custom-toast-position',
      });
      this.closeDialog(response);
    } else {
      this.toaster.error(response.detail, '', {
        positionClass: 'custom-toast-position'
      });
      this.closeDialog(response);
    }
  }
  

  onEventBasedConfigChange(checked: boolean) {
    if (!checked) {
      this.formData.patchValue({
        eventType: ''
      });
    }
  }

  onWorkflowChange() {
    const workflowId = this.formData.get('workflow')?.value;
    if (workflowId) {
      const workflow = this.sessions.find(session => session.workflow_id === workflowId);
      if (workflow) {
        // Assume some condition to determine the occurrence type based on the workflow details
        const occurrenceType = workflow.someCondition ? 'RECURRING' : 'ONCE';
        this.formData.patchValue({ occurrenceType });
      }
    }
  }
  
  closeDialog(result: any): void {
    this.addEvent.emit(result);
    this.dialogRef.close();
  }


  getCronDayId(day: string) : number {
    switch (day) {
      case 'S':
          return 0; // Sunday
      case 'M':
          return 1; // Monday
      case 'T':
          return 2; // Tuesday
      case 'W':
          return 3; // Wednesday
      case 'R':
          return 4; // Thursday
      case 'F':
          return 5; // Friday
      case 'A':
          return 6; // Saturday
      default:
          return -1;
    }
  }

  getCronDay(dayId: number) {
    switch (dayId) {
      case 0:
          return 'S'; // Sunday
      case 1:
          return 'M'; // Monday
      case 2:
          return 'T'; // Tuesday
      case 3:
          return 'W'; // Wednesday
      case 4:
          return 'R'; // Thursday
      case 5:
          return 'F'; // Friday
      case 6:
          return 'A'; // Saturday
      default:
          return '';
    }
  }

  generateCronExpression(repeatEvery: number, repeatType: string, weekDays: string[]): string {
    let cronExpression = '';

    // Convert weekDays abbreviations to cron format (0-6, where 1 is Monday 6 is Saturday and 0 is Sunday)
    let cronWeekDays = weekDays.map(day => {
        return this.getCronDayId(day).toString();
    }).join(',');

    // If weekDays array is empty, include all days of the week
    if (weekDays.length === 0) {
        cronWeekDays = '0,1,2,3,4,5,6'; // All days of the week
    }

    // Construct the cron expression based on the repeatType
    switch (repeatType) {
        case 'Days':
            // Example: "0 12 */2 * 0-6" (every 2 days)
            cronExpression = `0 12 */${repeatEvery} * ${cronWeekDays}`;
            break;
        case 'Weeks':
            // Example: "0 12 * * 2,6,0" (every 2 weeks on Tuesday, Saturday, and Sunday)
            cronExpression = `0 12 * * */${repeatEvery} ${cronWeekDays}`;
            break;
        case 'Months':
            // Example: "0 12 1 */2 0-6" (every 2 months on the 1st day)
            cronExpression = `0 12 1 */${repeatEvery} ${cronWeekDays}`;
            break;
        case 'Years':
            // Example: "0 12 1 1 */2 0-6" (every 2 years on January 1st)
            cronExpression = `0 12 1 1 */${repeatEvery} ${cronWeekDays}`;
            break;
        default:
            // Handle other repeat types here if necessary
            break;
    }

    return cronExpression;
}

filterNode(
  nodes: FileStructureNodeResponse[],
  filterText: string,
): FileStructureNodeResponse[] {
  const filteredNodes: FileStructureNodeResponse[] = [];

  nodes.forEach((node: any) => {
    const children = node.children
      ? this.filterNode(node.children, filterText)
      : [];

    if (
      node.name.toLowerCase().includes(filterText.toLowerCase()) ||
      children.length > 0
    ) {
      const newNode = { ...node, children };
      filteredNodes.push(newNode);
    }
  });

  return filteredNodes;
}

filterNodes(event: Event) { console.log(event,"event mos");
  const filterText = (event.target as HTMLInputElement)?.value;
  if (!filterText) {
    this.dataSource.data = this.files;
    this.treeControl.expandAll();
  } else {
    this.dataSource.data = this.filterNode(this.files, filterText);
    this.treeControl.dataNodes = this.dataSource.data;
    this.treeControl.expandAll();
  }
}


isFileSelected(node: FileStructureNodeResponse) {
  this.folderPath = node.full_path;
  return this.selection.isSelected(node);
}

toggleFileSelection(node: any) {
  this.selection.toggle(node);
  if (node.type === 'file') {
    this.path = node.full_path;
  } else if (node.type === 'folder') {
    this.path = node.full_path;
  }
}

onOccurrenceTypeChange(event: MatSelectChange) {
  if(event.value === 'RECURRING'){
    this.enableSchedule = true;
  }
  if(event.value === 'ONCE'){
    this.enbaleScheduleforOnce()
  }
}

onOnceTypeTimeChange() {
  this.enbaleScheduleforOnce();
}

enbaleScheduleforOnce(){
  let onceDate = this.formData.get('onceDateTime')?.value;
  let onceTime = this.formData.get('time')?.value;
  this.enableSchedule = onceDate && onceTime
}

}
