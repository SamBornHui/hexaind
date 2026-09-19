import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { DataService } from '../../pages/data/services/data.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';

import { ConfigService } from 'src/app/services/config.service';

import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { MatTableDataSource } from '@angular/material/table';
import { catchError, map, tap } from 'rxjs/operators';


@Component({
  selector: 'app-saved-workflow-templates-dialog',
  templateUrl: './load-saved-templates-dialog.component.html',
  styleUrls: ['./load-saved-templates-dialog.component.less']
})
export class LoadWorkflowTemplatesDialogComponent {
  private searchTerms = new Subject<string>();
  searchText: string = '';
  dataSource: any;
  displayedColumns: string[] = [
    'name',
    'description',
    'preview',
  ];
  selectedRow: any
  sessions:any;
  preview:boolean = false;
  templateImage:any;


  constructor( 
    private workflowService: WorkflowsSessionsApiService, 
    public dialogRef: MatDialogRef<LoadWorkflowTemplatesDialogComponent>,
    private configService:ConfigService) {
    this.searchTerms.pipe(debounceTime(300)).subscribe((term) => {
      this.dataSource.filter = term.trim().toLowerCase();
    });
  }

  ngOnInit() {
    this.getTemplates()
  }

  async getTemplates() {
    let templates = await this.workflowService.GetWorkflowTemplates(this.configService.SelectedSiteId,this.configService.SelectedProjectId);
    if(templates) {
      this.sessions = templates?.sessions;
      this.dataSource = new MatTableDataSource(this.sessions);
    }    
  }
  onPreviewWorkflowTemplate(element:any){
    this.workflowService
    .getTemplateImageContent({path: element.template_screenshot, name: ''})
    .subscribe(
      (result) => {
        this.templateImage = result;
        this.preview = true;
      },
      (error) => {
        console.error('Error fetching image content:', error);
      },
    );
  }
  onRadioChange(row: any) {
    this.selectedRow = row
  }

  async onSubmit() {
    let workflow = await this.workflowService.GetWorkflowById(this.configService.SelectedSiteId,this.configService.SelectedProjectId!,this.selectedRow.workflow_id);
    if(workflow){
      this.dialogRef.close({success: true, 'workflow': workflow})
    }
  }
}
