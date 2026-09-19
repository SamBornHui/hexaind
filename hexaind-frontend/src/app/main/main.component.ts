import { Component } from '@angular/core';
import { NavService } from '../controls/left-nav/nav.service';
import { Project } from '../models/project-models';

export enum Page {
  AdminConnectors,
  AdminSettings,
  AdminUsers,
  Connectors,
  Help,
  JuypterNotebook,
  Notifications,
  Settings,
  Workflows,
  Data,
  Models,
  Tools,
  WorkflowRunView,
  CustomPythonRecipes,
  DataStructure,
}

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.less'],
})
export class MainComponent {
  test: boolean = true;

  constructor(public navService: NavService) {
    let currentUser = {
      _id: '65967ecac48951a0928b7dac',
      name: 'Databrick Admin',
      email: 'databrickadmin@databrick.tech',
      created_by: 'databrickadmin@databrick.tech',
      is_active: 1,
      login_status: true,
      is_super_admin: true,
      first_name: 'Databrick',
      last_name: 'Admin',
    };
  }

  onCloseCreateNewWorkflowDialog() {
    this.test = false;
  }
}
