import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ApiService } from 'src/app/services/api.service';
import { NewConnectorService } from '../connector-dialog/services/new-connector.service';
import { ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';

@Component({
  selector: 'app-big-query-load-saved-query',
  templateUrl: './big-query-load-saved-query.component.html',
  styleUrls: ['./big-query-load-saved-query.component.less']
})
export class BigQueryLoadSavedQueryComponent {

  project1: string='';
  project2: string='';
  currentUser: any;
  siteId: any;
  projects: any;
  currentProjectId:any;
  currentQueryId: any;
  getQueries: any;
  displayQuery: any;
  query_params: any;
  loadQueryFileName: any;
  searchTerms: string | undefined;
  runQuery: any;
  lastRunParameter: any = 'Last Run';
  constructor(
    public dialogRef: MatDialogRef<BigQueryLoadSavedQueryComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private apiService: ApiService,
    private connectorService: NewConnectorService,
    private configService: ConfigService,
  ) {}
  load: any = this.data.load;
  title: string  = this.data.title;
  close(): void {
    this.dialogRef.close();
  }
  
  ngOnInit(){
    this.getprojects();
  }
  async getprojects(){
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!) as any;
    const jsonData = {
      id: this.currentUser._id,
      get_details: true,
    };
    this.projects = await this.apiService.GetProjects(
      '1',
      this.searchTerms,
      jsonData,
    );
  }
  async getProjectQueries(projectId : any){
    this.currentProjectId = projectId;
    this.siteId = this.configService.SelectedSiteId;
    this.getQueries = await this.connectorService.getallqueries(
      this.siteId, 
      projectId,
      this.data.connectorId,
    );
    this.getQueries = this.getQueries.queries;
    this.displayQuery='';
    console.log("get queries, ", this.getQueries);
  }

  lastRunOption(){
    this.lastRunParameter = 'Last Run'
    this.runQuery = 'SELECT * FROM orders WHERE order_date BETWEEN LASTRUN AND CURRENT_DATE;'
  }

  getDisplayQueries(query : any){
    this.loadQueryFileName = query.name;
    this.query_params = query.query_params;
    this.getQueries.filter((session : any)=>{
      if(session._id == query._id){
        this.currentQueryId = query._id
        this.displayQuery = session.query;
      }
    })
  }
  onLoad(){
    
    this.dialogRef.close({
      success: true,
      projectId : this.currentProjectId,
      queryId: this.currentQueryId,
      displayQuery: this.displayQuery,
      query_params: this.query_params,
      loadQueryFileName: this.loadQueryFileName 
    });
  }

}
