import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { ProjectsComponent } from './pages/projects/projects.component';
import { ChangePasswordComponent } from './dialogs/change-password/change-password.component';
import { ComponentsComponent } from './components/components.component';
import { AuthGuard } from './pages/guards/index';
import { RegisterAccountComponent } from './pages/register-account/register-account.component';
import { CustomCodeWidgetBuilderComponent } from './pages/custom-code-widget-builder/custom-code-widget-builder.component';
import { WorkflowRunsViewComponent } from './pages/workflow-runs-view/workflow-runs-view.component';
import { CustomPythonRecipeComponent } from './pages/custom-python-recipe/custom-python-recipe.component';
import { DataSheetGeneratorComponent } from './pages/tools/data-sheet-generator/data-sheet-generator.component';
import { ResetPasswordComponent } from './pages/reset-password/reset-password.component';
import { ManageAccessComponent } from './pages/manage-access/manage-access.component';
import { UsersComponent } from './pages/users/users.component';
import { RolesComponent } from './pages/roles/roles.component';
import { ConverterComponent } from './pages/tools/data-sheet-generator/converter/converter.component';
import { DsgFilesComponent } from './pages/tools/data-sheet-generator/dsg-files/dsg-files.component';
import { Uc6Component } from './pages/uc6/uc6.component';
import { Uc7Component } from './pages/uc7/uc7.component';
import { Uc12Component } from './pages/uc12/uc12.component';
import { UC1TrainPredictionsComponent } from './pages/uc1-models-predictions/uc1-models-predictions.component';
import { DataCatalogComponent } from './pages/tools/data-catalog/data-catalog.component';
import { Uc2ResultsComponent } from './pages/uc2-results/uc2-results.component';
import { Uc2ResultsNewComponent } from './pages/uc2-results-new/uc2-results-new.component';
import { Uc3DashboardComponent } from './pages/uc3-dashboard/uc3-dashboard.component';

import { ScrapAnalysisComponent } from './pages/tools/scrap-analysis/scrap-analysis.component';
import { ActivityLogsComponent } from './pages/tools/data-sheet-generator/activity-logs/activity-logs.component';


const routes: Routes = [
  { path: 'login', component: LoginComponent },

  {
    path: 'sites/:siteId/projects/:projectId',
    canActivate: [AuthGuard],
    loadChildren: () => import('./main/main.module').then((m) => m.MainModule),
  },

  { path: '', canActivate: [AuthGuard], component: ProjectsComponent },
  { path: 'change-password', component: ChangePasswordComponent },
  {
    path: 'sites/:siteId/projects/:projectId/data-sheet-generator',
    canActivate: [AuthGuard],
    component: DataSheetGeneratorComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/scrap-analysis',
    canActivate: [AuthGuard],
    component: ScrapAnalysisComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/data-sheets',
    canActivate: [AuthGuard],
    component: DsgFilesComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/workflows',
    canActivate: [AuthGuard],
    loadChildren: () => import('./main/main.module').then((m) => m.MainModule),
  },
  {
    path: 'sites/:siteId/projects/:projectId/jobs',
    canActivate: [AuthGuard],
    loadChildren: () => import('./main/main.module').then((m) => m.MainModule),
  },
  {
    path: 'workflow-designer',
    canActivate: [AuthGuard],
    loadChildren: () =>
      import('./pages/workflow-designer/workflow-designer.module').then(
        (m) => m.WorkflowDesignerModule,
      ),
  },
  {
    path: 'sites/:siteId/projects/:projectId/workflows-run/:id',
    canActivate: [AuthGuard],
    component: WorkflowRunsViewComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/custom-python-recipe',
    canActivate: [AuthGuard],
    component: CustomPythonRecipeComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/custom-code-builder/:customWidgetId/:viewMode',
    canActivate: [AuthGuard],
    component: CustomCodeWidgetBuilderComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/train-predictions',
    canActivate: [AuthGuard],
    component: UC1TrainPredictionsComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/uc2-results',
    canActivate: [AuthGuard],
    component: Uc2ResultsComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/uc2-results-new',
    canActivate: [AuthGuard],
    component: Uc2ResultsNewComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/uc3Dashboard',
    canActivate: [AuthGuard],
    component: Uc3DashboardComponent,
  },
  {
    path: 'manage-users',
    canActivate: [AuthGuard],
    component: UsersComponent,
  },
  {
    path: 'roles',
    canActivate: [AuthGuard],
    component: RolesComponent,
  },
  { path: 'components', component: ComponentsComponent },
  { path: 'users/register-account', component: RegisterAccountComponent },
  { path: 'users/password/edit', component: ResetPasswordComponent },
  // { path: 'manage-access', component: ManageAccessComponent },
  {
    path: 'sites/:siteId/projects/:projectId/manage-access',
    canActivate: [AuthGuard],
    component: ManageAccessComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/converter',
    canActivate: [AuthGuard],
    component: ConverterComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/image-analysis/:datasetId/:feature',
    canActivate: [AuthGuard],
    loadChildren: () =>
      import('./pages/images/images.module').then(
        (m) => m.ImagesModule,
      ),
  },
  {
    path: 'sites/:siteId/projects/:projectId/UC6',
    canActivate: [AuthGuard],
    component: Uc6Component,
  },
  {
    path: 'sites/:siteId/projects/:projectId/UC7',
    canActivate: [AuthGuard],
    component: Uc7Component,
  },
  {
    path: 'sites/:siteId/projects/:projectId/UC12',
    canActivate: [AuthGuard],
    component: Uc12Component,
  },
  {
    path: 'sites/:siteId/projects/:projectId/data-catalog',
    canActivate: [AuthGuard],
    component: DataCatalogComponent,
  },
  {
    path: 'sites/:siteId/projects/:projectId/activity-logs',
    canActivate: [AuthGuard],
    component: ActivityLogsComponent,
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule { }
