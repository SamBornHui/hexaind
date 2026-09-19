// main.module.ts
import { NgModule } from '@angular/core';
import { SharedModule } from '../shared.module';
import { MainComponent } from './main.component';
import { MatTableModule } from '@angular/material/table';
import { ToastrModule } from 'ngx-toastr';
import { RouterModule, Routes } from '@angular/router';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { NgxMaterialTimepickerModule } from 'ngx-material-timepicker';
import { CreateNewWorkflowSessionComponent } from '../dialogs/create-new-workflow/create-new-workflow-session.component';
import { UpdateWorkflowSessionComponent } from '../dialogs/update-workflow-session/update-workflow-session.component';
import { AdminUsersComponent } from '../pages/admin-users/admin-users.component';
import { AddUserComponent } from '../dialogs/add-user/add-user.component';
import { WorkflowRunPreviewComponent } from '../dialogs/workflow-run-preview/workflow-run-preview.component';
import { NotificationsComponent } from '../pages/notifications/notifications.component';
import { NotificationDetailsComponent } from '../pages/notifications/notification-details/notification-details.component';
import { DataComponent } from '../pages/data/data.component';
import { ModelsComponent } from '../pages/models/models.component';
import { ConnectorsComponent } from '../pages/connectors/connectors.component';
import { ConnectorDialogComponent } from '../dialogs/connector-dialog/connector-dialog.component';
import { ProjectsComponent } from '../pages/projects/projects.component';
import { CreateNewProjectComponent } from '../dialogs/create-new-project/create-new-project.component';
import { CreateNewPasswordComponent } from '../dialogs/create-new-password/create-new-password.component';
import { CopyPasswordComponent } from '../dialogs/copy-password/copy-password.component';
import { DataImportDialogComponent } from '../dialogs/data-import/data-import-dialog.component';
import { ToolsComponent } from '../pages/tools/tools.component';
import { ShowDatasetDialogComponent } from '../dialogs/show-dataset-dialog/show-dataset-dialog.component';
import { ModuleImportDialogComponent } from '../dialogs/module-import-dialog/module-import-dialog.component';
import { ShowModuleDialogComponent } from '../dialogs/show-module-dialog/show-module-dialog.component';
import { JupyterNotebooksComponent } from '../pages/jupyter-notebooks/jupyter-notebooks.component';
import { CustomCodeWidgetBuilderComponent } from '../pages/custom-code-widget-builder/custom-code-widget-builder.component';
import { CustomPythonRecipeComponent } from '../pages/custom-python-recipe/custom-python-recipe.component';
import { WorkflowRunsViewComponent } from '../pages/workflow-runs-view/workflow-runs-view.component';
import { UsersComponent } from '../pages/users/users.component';
import { UpdateDatasetsComponent } from '../dialogs/update-datasets/update-datasets.component';
import { WorkflowComponent } from '../pages/workflows/workflow.component';
import { ManageAccessComponent } from '../pages/manage-access/manage-access.component';
import { grantAccessComponent } from '../dialogs/grant-access/grant-access.component';
import { grantServerAccessComponent } from '../dialogs/grant-server-access/grant-server-access.component';
import { RolesComponent } from '../pages/roles/roles.component';
import { JobsComponent } from '../pages/jobs/jobs.component';
import { CreateNewScheduleComponent } from '../dialogs/create-schedule/create-schedule.component';
import { ViewScheduleComponent } from '../dialogs/view-schedule/view-schedule.component';
import { PublishWorkflowComponent } from '../dialogs/publish-workflow/publish-workflow.component';
import { UpdateWorkflowComponent } from '../dialogs/update-workflow/update-workflow.component';
import { PublishedWorkflowRunsComponent } from '../dialogs/published-workflow-runs/published-workflow-runs.component';
import { RunSummaryComponent } from '../dialogs/run-summary/run-summary.component';
import { FileSizePipe } from '../pipes/file-size.pipe';
import { ConnectorsUpdateComponent } from '../dialogs/connectors-update/connectors-update.component';
import { DataStructureComponent } from '../pages/data-structure/data-structure.component';
import { ModelComparisonComponent } from '../pages/models/model-comparison/model-comparison.component';
import { EditImageFolderComponent } from '../dialogs/data-import/edit-image-folder/edit-image-folder.component';
import { ImagePreviewComponent } from '../dialogs/image-preview/image-preview.component';
import { CreateJupyterServer } from '../dialogs/create-jupyter-server/create-jupyter-server.component';
import { CreateJupyterNotebookComponent } from '../dialogs/create-jupyter-notebook/create-jupyter-notebook.component';
import { ImageVideoPreviewComponent } from '../dialogs/image-video-preview/image-video-preview.component';
import { UC1TrainPredictionsComponent } from '../pages/uc1-models-predictions/uc1-models-predictions.component';
import { ShareWorkflowTemplateComponent } from '../dialogs/share-workflow-template/share-workflow-template.component';
import { Uc6Component } from '../pages/uc6/uc6.component';
import { Uc7Component } from '../pages/uc7/uc7.component';
import { Uc2ResultsComponent } from '../pages/uc2-results/uc2-results.component';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';
import { CreateSessionComponent } from '../pages/create-session/create-session.component';
import { DataCatalogComponent } from '../pages/tools/data-catalog/data-catalog.component';
import { MatPaginatorModule } from '@angular/material/paginator';
import { TravelerStepsComponent } from '../pages/uc7/traveler-steps/traveler-steps.component';
import { SigmaCommonTestComponent } from '../pages/uc7/sigma-common-test/sigma-common-test.component';
import { AdvanceSearchComponent } from '../pages/uc7/advance-search/advance-search.component';
import { AdvanceSearchSigmaComponent } from '../pages/uc7/advance-search-sigma/advance-search-sigma.component';
import { AddToDatasetComponent } from '../pages/uc7/add-to-dataset/add-to-dataset.component';
import { Uc2ResultsNewComponent } from '../pages/uc2-results-new/uc2-results-new.component';
import { ScrapAnalysisComponent } from '../pages/tools/scrap-analysis/scrap-analysis.component';
import { ScrapRunVizualizationComponent } from '../pages/tools/scrap-analysis/scrap-scenario-run-visualization/scrap-scenario-run-visualization.component';
import { ScrapFilesComponent } from '../pages/tools/scrap-analysis/scrap-files/scrap-files.component';
import { scrapScenarioComponent } from '../pages/tools/scrap-analysis/scrap-scenarios/scrap-scenarios.component';
import { ScrapRunsComponent } from '../pages/tools/scrap-analysis/scrap-scenario-runs/scrap-runs.component';
import { FilteredItemsPipe, Uc3DashboardComponent } from '../pages/uc3-dashboard/uc3-dashboard.component';
import { DataSheetGeneratorComponent } from '../pages/tools/data-sheet-generator/data-sheet-generator.component';
import { ConverterComponent } from '../pages/tools/data-sheet-generator/converter/converter.component';
import { DsgFilesComponent } from '../pages/tools/data-sheet-generator/dsg-files/dsg-files.component';
import { FileTreeNodeComponent } from '../pages/tools/data-sheet-generator/dsg-files/file-tree-node/file-tree-node.component';
import { ConfirmationDialogComponent } from '../pages/tools/data-sheet-generator/dsg-files/confirmation-dialog/confirmation-dialog.component';
import { ActivityLogsComponent } from '../pages/tools/data-sheet-generator/activity-logs/activity-logs.component';





const routes: Routes = [
  { path: '', redirectTo: 'workflows', pathMatch: 'full' },
  {
    path: '',
    component: MainComponent,
    children: [
      { path: 'data', component: DataComponent },
      { path: 'data-structure', component: DataStructureComponent },
      { path: 'models', component: ModelsComponent },
      { path: 'tools', component: ToolsComponent },
      { path: 'workflows', component: WorkflowComponent },
      { path: 'notifications', component: NotificationsComponent },
      { path: 'connectors', component: ConnectorsComponent },
      { path: 'admin-users', component: AdminUsersComponent },
      { path: 'jupyter-hub', component: JupyterNotebooksComponent },
      { path: 'custom-python-recipe', component: CustomPythonRecipeComponent },
      { path: 'users', component: UsersComponent },
      { path: 'manage-access', component: ManageAccessComponent },
      { path: 'roles', component: RolesComponent },
      { path: 'jobs', component: JobsComponent },
      // { path: 'train-predictions', component: UC1TrainPredictionsComponent },
      { path: 'uc6', component: Uc6Component },
      { path: 'uc7', component: Uc7Component },
    ],
  },
];

@NgModule({
  declarations: [
    DataSheetGeneratorComponent,
    ConverterComponent,
    DsgFilesComponent,
    FileTreeNodeComponent,
    FileSizePipe,
    MainComponent,
    WorkflowComponent,
    CreateNewWorkflowSessionComponent,
    WorkflowRunPreviewComponent,
    PublishedWorkflowRunsComponent,
    DataComponent,
    ModuleImportDialogComponent,
    ShowModuleDialogComponent,
    AdminUsersComponent,
    AddUserComponent,
    ModelsComponent,
    NotificationsComponent,
    ConnectorsComponent,
    ConnectorDialogComponent,
    UpdateWorkflowSessionComponent,
    UpdateWorkflowComponent,
    PublishWorkflowComponent,
    RunSummaryComponent,
    ProjectsComponent,
    CreateNewProjectComponent,
    CreateNewPasswordComponent,
    CopyPasswordComponent,
    DataImportDialogComponent,
    EditImageFolderComponent,
    ToolsComponent,
    ShowDatasetDialogComponent,
    JupyterNotebooksComponent,
    CustomCodeWidgetBuilderComponent,
    CustomPythonRecipeComponent,
    WorkflowRunsViewComponent,
    UsersComponent,
    UpdateDatasetsComponent,
    ManageAccessComponent,
    grantAccessComponent,
    grantServerAccessComponent,
    RolesComponent,
    JobsComponent,
    CreateNewScheduleComponent,
    ViewScheduleComponent,
    ConnectorsUpdateComponent,
    DataStructureComponent,
    ModelComparisonComponent,
    ImagePreviewComponent,
    CreateJupyterServer,
    UC1TrainPredictionsComponent,
    CreateJupyterNotebookComponent,
    ImageVideoPreviewComponent,
    Uc2ResultsComponent,
    ShareWorkflowTemplateComponent,
    Uc7Component,
    CreateSessionComponent,
    DataCatalogComponent,
    TravelerStepsComponent,
    SigmaCommonTestComponent,
    AdvanceSearchComponent,
    AddToDatasetComponent,
    AdvanceSearchSigmaComponent,
    Uc2ResultsNewComponent,
    ScrapAnalysisComponent,
    ScrapRunVizualizationComponent,
    ScrapFilesComponent,
    scrapScenarioComponent,
    ScrapRunsComponent,
    Uc3DashboardComponent,
    FilteredItemsPipe,
    ConfirmationDialogComponent,
    ActivityLogsComponent,
  ],

  imports: [
    SharedModule,
    RouterModule.forChild(routes),
    MatTableModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatInputModule,
    MatFormFieldModule,
    NgxMaterialTimepickerModule,
    ToastrModule.forRoot({
      closeButton: true,
      timeOut: 15000, // 15 seconds
      progressBar: true,
    }),
    NgMultiSelectDropDownModule,
    MatPaginatorModule,
    NotificationDetailsComponent
  ],
})
export class MainModule { }
