import { Component } from '@angular/core';
import { ProjectButtonVisibilityServiceService } from 'src/app/controls/header/project-button-visibility-service.service';

interface rolesData {
  entity: string;
  serverAdmin: boolean;
  ProjectAdmin: boolean;
  fullMember: boolean;
  limitedMember: boolean;
}

let ELEMENT_DATA: rolesData[] = [
  {entity: 'Datasets', serverAdmin: true, ProjectAdmin : true,  fullMember: true, limitedMember: true},
  {entity: 'Models', serverAdmin: true, ProjectAdmin : true, fullMember: true, limitedMember: true},
  {entity: 'Workflows', serverAdmin: true, ProjectAdmin : true, fullMember: true, limitedMember: true},
  {entity: 'Custom Widgets', serverAdmin: true, ProjectAdmin : true, fullMember: true, limitedMember: false},
  {entity: 'Connectors', serverAdmin: true, ProjectAdmin : true, fullMember: true, limitedMember: false},
  {entity: 'Jupyter Notebooks', serverAdmin: true, ProjectAdmin : true,  fullMember: true, limitedMember: false},
  {entity: 'Apps', serverAdmin: true, ProjectAdmin : true, fullMember: true, limitedMember: false},
  {entity: 'Projects', serverAdmin: true, ProjectAdmin : true,  fullMember: true, limitedMember: true},
  {entity: 'Manage Access', serverAdmin: true, ProjectAdmin : true, fullMember: false, limitedMember: false},
  {entity: 'Manage Users', serverAdmin: true, ProjectAdmin : false,  fullMember: false, limitedMember: false},
  {entity: 'Manage Projects', serverAdmin: true, ProjectAdmin : true, fullMember: false, limitedMember: false},
  {entity: 'Manage Roles', serverAdmin: true, ProjectAdmin : false,  fullMember: false, limitedMember: false}
];
@Component({
  selector: 'app-roles',
  templateUrl: './roles.component.html',
  styleUrls: ['./roles.component.less']
})
export class RolesComponent {
  constructor(
    private projectVisibilityService: ProjectButtonVisibilityServiceService
  ){
    //
  }
  displayedColumns: any[] = ['entity', 'serverAdmin','ProjectAdmin','fullMember', 'limitedMember'];
  display=['entity', 'serverAdmin','ProjectAdmin','fullMember', 'limitedMember']
  columns: string[] = ['name'];
  disabledMat = true
  dataSource = ELEMENT_DATA;

  ngOnInit() {
    this.projectVisibilityService.hideProjectsButton();
  }

  ngOnDestroy(): void {
    this.projectVisibilityService.showProjectsButton();
  }
}
