import { Component, EventEmitter, Input, OnInit, Output, ChangeDetectorRef, SimpleChanges } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { ViewFullImageDialogBox } from 'src/app/pages/images/segment/view-image-dialog-box/view-full-image-dialog-box.component';
import { WorkflowOutputdirDialogboxComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/manage-workflow/workflow-outputdir-dialogbox/workflow-outputdir-dialogbox.component';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { ConfigService } from 'src/app/services/config.service';



@Component({
  selector: 'workflows-grid',
  templateUrl: './workflows-grid.component.html',
  styleUrls: ['./workflows-grid.component.less'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', display: 'none' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ]
})
export class WorkflowsGridComponent implements OnInit {
  @Output() changeFavoriteEvent = new EventEmitter();
  @Output() expandedWorkflowEvent = new EventEmitter();
  @Output() manageAssignWorkflowEvent = new EventEmitter();
  @Output() assignWorkflowToImagesEvent = new EventEmitter();
  @Output() deleteWorkflowEvent = new EventEmitter();
  @Output() editWorkflowEventt = new EventEmitter();
  @Output() changeOutputDirEventt = new EventEmitter();

  @Input() datasetId: any;
  @Input() selectedFolderId: any;
  @Input() selectedFolderName: any;
  @Input() folderType: any;
  @Input() workflows: any;
  @Input() expandedWorkflowData: any;
  @Input() selectedSegmentImages: any;

  currentUser: any = {};
  dataSource!: MatTableDataSource<any>;
  imageDisplayUrl = '/imageAnalysis/showImage?file=';

  favoriteWorkflows = [];
  unfavoriteWorkflows = [];
  sortedWorkflows = [];
  initialWorkflows = [];

  favChanged = false;
  constructor(public dialog: MatDialog,
    public imageAnalysisService: ImageAnalysisService,
    private configService: ConfigService,
    private cdr: ChangeDetectorRef
  ) {
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.initialWorkflows = this.workflows;
    this.dataSource = new MatTableDataSource(this.workflows);
    // this.setWorkflowsTableData()
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['workflows']) {
      this.cdr.detectChanges();
      this.initialWorkflows = this.workflows;
      this.dataSource = new MatTableDataSource(this.workflows);
      // this.setWorkflowsTableData()
    }
  }
  

  convertTableToMatTable(data: any) {
    return new MatTableDataSource(data);
  }
  isFavorited(favorited_by:any[]){
    const favoriteUser = favorited_by.filter(
      (item:any) => item.user_id == this.currentUser._id && item.favorite == true
    );
    return (favoriteUser.length>0)?true:false;     
  }
  changeFavorite(workflow: any) {
    let addFav = (this.isFavorited(workflow.favorited_by))?false:true;
    this.favChanged = true;
    if (!this.expandedWorkflowData['manageWorkflow']) {
      this.changeFavoriteEvent.emit({ favType: addFav, workflow: workflow });
    }
  }

  expandedWorkflow(workflow: any) {
    if (!this.expandedWorkflowData['manageWorkflow']) {
      this.expandedWorkflowEvent.emit(workflow);
      this.getImageContent(workflow, 'orignal_thumb');
      this.getImageContent(workflow, 'segment_thumb');
    }
  }

  manageAssignWorkflow(workflow: any) {
    this.manageAssignWorkflowEvent.emit(workflow)
  }

  assignWorkflowToImages(workflow: any, selectedSegmentImages: any, aftersavingwf: any, fromOtherFolder: any, removeApppliedStatus: any) {
    if (workflow['dataset_id'] != this.datasetId) {
      fromOtherFolder = true;
    } else if (workflow['foldername'] != this.selectedFolderName) {
      fromOtherFolder = true;
    }
    this.assignWorkflowToImagesEvent.emit(
      { workflow: workflow, selectedSegmentImages: selectedSegmentImages, aftersavingwf: aftersavingwf, fromOtherFolder: fromOtherFolder, removeApppliedStatus: removeApppliedStatus }
    )
  }

  getImageContent(obj: any, key: string) {
    let path = obj[key];
    if (path && path != '') {
      this.imageAnalysisService
        .getIndividualImageContent({ path: path, name: '' })
        .subscribe(
          (result) => {
            let newPathKey = key + '_url'
            obj[newPathKey] = '';
            obj[newPathKey] = result;
          },
          (error) => {
            console.error('Error fetching image content:', error);
          },
        );
    }
  }
  imageFullView(workflow: any) {

    if (!workflow['orig_full_url'] || workflow['seg_full_url']) {
      this.getImageContent(workflow, 'orig_full')
      this.getImageContent(workflow, 'seg_full')
      setTimeout(() => {
        let details = {
          'diplayedImagesType': 2,
          'rawImage': workflow['orig_full_url'],
          'segmentedImage': workflow['seg_full_url'],
          "workflowName": workflow['Wname']
        }
        const dialogRef = this.dialog.open(ViewFullImageDialogBox, {
          width: '75vw',
          maxWidth: '75vw',
          height: '75%',
          backdropClass: "add-data-set-backdrop",
          panelClass: 'add-data-set-panel-class',
          data: details
        });
        dialogRef.afterClosed().subscribe(_dialogResult => {
    
        });
      }, 1000);
    }


  }

  deleteWorkflow(workflow:any) {
    if (!this.expandedWorkflowData['manageWorkflow']) {
      this.deleteWorkflowEvent.emit(workflow);
    }
    let project_id = this.configService.SelectedProjectId;
    // this.imageAnalysisService.updateLastAccess({'dataset_id' : this.datasetId , 'project_id' : project_id}).subscribe();
  }

  editWorkfloww(type:any, workflowData:any) {
    if (!this.expandedWorkflowData['manageWorkflow'] && this.folderType == 1) {
      this.editWorkflowEventt.emit({ type: type, workflowData: workflowData });
    }
  }

  editDirectory(workflowData:any) {
    if (!this.expandedWorkflowData['manageWorkflow']) {
      if (workflowData['output_directory_options'] == undefined) {
        workflowData['output_directory_options'] = {
          "setDirectory": false,
          "defaultDirectory": true,
          "outputDirectory": ""
        }
      }
      const dialogRef = this.dialog.open(WorkflowOutputdirDialogboxComponent, {
        width: '30%',
        disableClose: true,
        panelClass: "add-data-set-panel-class",
        data: { "outputDirOptions": workflowData['output_directory_options'] }
      });

      dialogRef.afterClosed().subscribe(result => {
        if (result != undefined) {
          this.changeOutputDirEventt.emit({ 'workflow': workflowData, 'outputDirOptions': result['outputDirOptions'] });
        }
      });
    }
  }

  setWorkflowsTableData() {
    this.favoriteWorkflows = this.initialWorkflows.filter((workflow:any) =>
      workflow.favorited_by.some(
        (fav:any) => fav.favorite
      )
    );
    this.unfavoriteWorkflows = this.initialWorkflows.filter((workflow:any) =>
      workflow.favorited_by.some(
        (fav:any) => !fav.favorite
      )
    );
  }

  sortData(sort: Sort) {
    const data = this.workflows.slice();
    if (!sort.active || sort.direction === '') {
      this.dataSource.data = data;
      return;
    }

    this.dataSource.data = data.sort((a: { [x: string]: string | number | Date; }, b: { [x: string]: string | number | Date; }) => {
      const isAsc = sort.direction === 'asc';
      return this.compare(a[sort.active], b[sort.active], isAsc);
    });
  }

  compare(a: number | string | Date, b: number | string | Date, isAsc: boolean) {
    // return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
    // equal items sort equally

    a = (typeof a === 'string') ? a.toUpperCase() : a; // Handle strings
    b = (typeof b === 'string') ? b.toUpperCase() : b; // Handle strings

    if (a === b) {
      return 0;
    }
    else if (a === undefined) {
      return 1;
    }
    else if (b === undefined) {
      return -1;
    }
    // nulls sort after anything else
    else if (a === null) {
      return 1;
    } else if (b === null) {
      return -1;
    }
    // otherwise, if we're ascending, lowest sorts first
    else if (isAsc) {
      return a < b ? -1 : 1;
    }
    // if descending, highest sorts first
    else {
      return a < b ? 1 : -1;
    }
  }
}
