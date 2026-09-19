// workflow-designer.module.ts
import { NgModule } from '@angular/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { WorkflowDesignerComponent } from './workflow-designer.component';
import { SharedModule } from '../../shared.module';
import { ColorPickerModule } from 'ngx-color-picker';
import { RouterModule, Routes } from '@angular/router';
import { BigQueryConfigComponent } from 'src/app/controls/configs/big-query-config/big-query-config.component';
import { CsvDataConfigComponent } from 'src/app/controls/configs/csv-data-config/csv-data-config.component';
import { JupyterConfigComponent } from 'src/app/controls/configs/jupyter-data-config/jupyter-data-config.component';
import { FilterConfigComponent } from 'src/app/controls/configs/filter-config/filter-config.component';
import { MountedDriveFileSelectorComponent } from 'src/app/dialogs/mounted-drive-file-selector/mounted-drive-file-selector.component';
import { TreeNodeComponent } from 'src/app/controls/tree-node/tree-node.component';
import { InjestionDialogComponent } from '../../dialogs/injestion-dialog/injestion-dialog.component';
import { SaveConfigComponent } from 'src/app/controls/configs/save-config/save-config.component';
import { PythonConfigComponent } from 'src/app/controls/configs/python-config/python-config.component';
import { MoboConfigComponent } from 'src/app/controls/configs/mobo-config/mobo-config.component';
import { CustomCodeConfigComponent } from 'src/app/controls/configs/custom-code-config/custom-code-config.component';
import { RescaleConfigComponent } from 'src/app/controls/configs/rescale-config/rescale-config.component';
import { WorkflowService } from 'src/app/services/workflow.service';
import * as PlotlyJS from 'plotly.js-dist-min';
import { PlotlyModule } from 'angular-plotly.js';
PlotlyModule.plotlyjs = PlotlyJS;
import { PostRescaleConfigComponent } from 'src/app/controls/configs/post-rescale-config/post-rescale-config.component';
import { DecisionConfigComponent } from 'src/app/controls/configs/decision-config/decision-config.component';
import { FeatureEngineeringConfigComponent } from 'src/app/controls/configs/feature-engineering-config/feature-engineering-config.component';
import { ConfigsInformationComponent } from 'src/app/controls/configs/configs-information/configs-information.component';
import { SettingsComponent } from 'src/app/controls/configs/settings/settings.component';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { DataPreviewDataComponent } from 'src/app/dialogs/data-preview/data/data.component';
import { MetadataComponent } from 'src/app/dialogs/data-preview/metadata/metadata.component';
import { StatisticsSchemaComponent } from 'src/app/dialogs/data-preview/statistics-schema/statistics-schema.component';
import { VisualizeComponent } from 'src/app/dialogs/data-preview/visualize/visualize.component';
import { PlatformFilesDialogComponent } from '../../dialogs/platform-files-dialog/platform-files-dialog.component';
import { AppendComponent } from 'src/app/controls/configs/append-config/append-config.component';
import { MatchingModelsDialogComponent } from '../../dialogs/matching-models-dialog/matching-models-dialog.component';
import { CreateNewWorkflowTemplateComponent } from '../../dialogs/create-new-workflow-template/create-new-workflow-template.component';
import { LoadWorkflowTemplatesDialogComponent } from '../../dialogs/load-saved-templates/load-saved-templates-dialog.component';
import { DataVisualizationComponent } from '../../dialogs/data-visualization/data-visualization.component';


import {
  AppendWidgetConfig,
  DatasetResult,
} from 'src/app/models/workflow-models';
import { LoopStartConfigComponent } from 'src/app/controls/configs/loop-start-config/loop-start-config.component';
import { LoopEndConfigComponent } from 'src/app/controls/configs/loop-end-config/loop-end-config.component';
import { MountedDriveDataPreviewComponent } from 'src/app/dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import { JoinComponent } from 'src/app/controls/configs/join-config/join.component';
import { ComparisonInstanceComponent } from 'src/app/dialogs/data-preview/visualize/comparison-instance/comparison-instance.component';
import { CorrelationComponent } from 'src/app/dialogs/data-preview/correlation/correlation.component';
import { ThermoCalcConfigComponent } from 'src/app/controls/configs/thermocalc-config/thermocalc-config.component';
import { AddUsersComponent } from 'src/app/dialogs/add-users/add-users.component';
import { EditUserComponent } from 'src/app/dialogs/edit-user/edit-user.component';
import { ActiveLearningConfigComponent } from 'src/app/controls/configs/active-learning-config/active-learning-config.component';
import { GprConfigComponent } from 'src/app/controls/configs/gpr-config/gpr-config.component';
import { MprConfigComponent } from 'src/app/controls/configs/mpr-config/mpr-config.component';
import { ExecutionStatusComponent } from 'src/app/controls/execution-status/execution-status.component';
import { ConfigActionBarComponent } from 'src/app/controls/configs/config-action-bar/config-action-bar.component';
import { DataSetResultsComponent } from 'src/app/dialogs/data-set-results/data-set-results/data-set-results.component';
import { DownloadRescaleVisualizeDataComponent } from 'src/app/dialogs/data-preview/download-rescale-vizualize-data/download-rescale-vizualize-data.component';
import { AutoMlConfigComponent } from 'src/app/controls/configs/auto-ml-config/auto-ml-config.component';
import { ModelPreviewDialogBoxComponent } from 'src/app/dialogs/model-preview-dialog-box/model-preview-dialog-box.component';
import { VisualizeTextdataComponent } from 'src/app/dialogs/data-preview/visualize/visualize-textdata/visualize-textdata.component';

import { CreateFolderDialogComponent } from 'src/app/dialogs/create-folder-dialog/create-folder-dialog.component';
import { ImportDatasetDialogComponent } from 'src/app/dialogs/import-dataset-dialog/import-dataset-dialog.component';
import { MoveDatasetDialogComponent } from 'src/app/dialogs/move-dataset-dialog/move-dataset-dialog.component';
import { DuplicateDatasetDialogComponent } from 'src/app/dialogs/duplicate-dataset-dialog/duplicate-dataset-dialog.component';
import { RenameFolderDialogComponent } from 'src/app/dialogs/rename-folder-dialog/rename-folder-dialog.component';
import { RfMlConfigComponent } from 'src/app/controls/configs/rf-ml-config/rf-ml-config.component';
import { NnrMlConfigComponent } from 'src/app/controls/configs/nnr-ml-config/nnr-ml-config.component';
import { XgboostMlConfigComponent } from 'src/app/controls/configs/xgboost-ml-config/xgboost-ml-config.component';
import { CatBoostMlConfigComponent } from 'src/app/controls/configs/cat-boost-ml-config/cat-boost-ml-config.component';
import { KnNeighborsMlConfigComponent } from 'src/app/controls/configs/kn-neighbors-ml-config/kn-neighbors-ml-config.component';
import { ExtraTreesMlConfigComponent } from 'src/app/controls/configs/extra-trees-ml-config/extra-trees-ml-config.component';
import { MatPaginatorModule } from '@angular/material/paginator';


import { LGBMMlConfigComponent } from 'src/app/controls/configs/lgbm-ml-config/lgbm-ml-config.component';
import { LRMlConfigComponent } from 'src/app/controls/configs/lr-ml-config/lr-ml-config.component';
import { NnTorchMlConfigComponent } from 'src/app/controls/configs/nntorch-ml-config/nntorch-ml-config.component';
import { ArimaMlConfigComponent } from 'src/app/controls/configs/arima-ml-config/arima-ml-config.component';
import { PreviewModelComparisionComponent } from 'src/app/dialogs/model-preview-dialog-box/preview-model-comparision/preview-model-comparision.component';
import { PredictionConfigComponent } from 'src/app/controls/configs/prediction-config/prediction-config.component';
import { SvmConfigComponent } from 'src/app/controls/configs/svm-config/svm-config.component';
import { GaussianProcessClassificationConfigComponent } from 'src/app/controls/configs/gaussian-process-classification-config/gaussian-process-classification-config.component';
import { UC2SigmaDataPreviewComponent } from '../uc7/uc2-sigma-data-preview/uc2-sigma-data-preview.component';
import { DropColumnsConfigComponent } from 'src/app/controls/configs/drop-columns-config/drop-columns-config.component';
import { DropMissingConfigComponent } from 'src/app/controls/configs/drop-missing-config/drop-missing-config.component';
import { ParquetWidgetConfigComponent } from 'src/app/controls/configs/parquet-widget-config/parquet-widget-config.component';
import { RenameColumnsConfigComponent } from 'src/app/controls/configs/rename-columns-config/rename-columns-config.component';
import { DatatypeConversionConfigComponent } from 'src/app/controls/configs/datatype-conversion-config/datatype-conversion-config.component';
import { Uc3ProbeModelPopupComponent } from '../uc7/uc3-probe-model-popup/uc3-probe-model-popup.component';
import { ExcelWidgetConfigComponent } from 'src/app/controls/configs/excel-widget-config/excel-widget-config.component';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { FilterSelectionConfigComponent } from 'src/app/controls/configs/filter-selection-config/filter-selection-config.component';
import { EditModelComponent } from '../../dialogs/edit-model/edit-model.component';
import { ColorSketchModule } from 'ngx-color/sketch';
import { ImageDatasetSelectionWidgetComponent } from 'src/app/controls/configs/image-dataset-selection-widget/image-dataset-selection-widget.component';
import { ImageRegionPropertiesWidgetComponent } from 'src/app/controls/configs/image-region-properties-widget/image-region-properties-widget.component';
import { ImageSpatialWidgetComponent } from 'src/app/controls/configs/image-spatial-widget/image-spatial-widget.component';
import { TextWidgetConfigComponent } from '../../controls/configs/text-widget-config/text-widget-config.component';

const routes: Routes = [
  {
    path: '',
    component: WorkflowDesignerComponent,
  },
];

@NgModule({
  declarations: [
    ExecutionStatusComponent,
    WorkflowDesignerComponent,
    BigQueryConfigComponent,
    ConfigActionBarComponent,
    FilterConfigComponent,
    DropMissingConfigComponent,
    JoinComponent,
    LoopStartConfigComponent,
    LoopEndConfigComponent,
    MountedDriveFileSelectorComponent,
    TreeNodeComponent,
    InjestionDialogComponent,
    CsvDataConfigComponent,
    JupyterConfigComponent,
    SaveConfigComponent,
    PythonConfigComponent,
    MoboConfigComponent,
    CustomCodeConfigComponent,
    RescaleConfigComponent,
    DecisionConfigComponent,
    UC2SigmaDataPreviewComponent,
    Uc3ProbeModelPopupComponent,
    FeatureEngineeringConfigComponent,
    PostRescaleConfigComponent,
    ConfigsInformationComponent,
    SettingsComponent,
    DataPreviewComponent,
    DataPreviewDataComponent,
    MetadataComponent,
    StatisticsSchemaComponent,
    VisualizeComponent,
    AppendComponent,
    PlatformFilesDialogComponent,
    AppendComponent,
    MountedDriveDataPreviewComponent,
    DataSetResultsComponent,
    ComparisonInstanceComponent,
    CorrelationComponent,
    ThermoCalcConfigComponent,
    AddUsersComponent,
    EditUserComponent,
    ActiveLearningConfigComponent,
    GprConfigComponent,
    MprConfigComponent,
    DownloadRescaleVisualizeDataComponent,
    CreateFolderDialogComponent,
    ImportDatasetDialogComponent,
    MoveDatasetDialogComponent,
    DuplicateDatasetDialogComponent,
    VisualizeTextdataComponent,
    RenameFolderDialogComponent,
    AutoMlConfigComponent,
    DownloadRescaleVisualizeDataComponent,
    VisualizeTextdataComponent,
    ModelPreviewDialogBoxComponent,
    LGBMMlConfigComponent,
    LRMlConfigComponent,
    RfMlConfigComponent,
    NnrMlConfigComponent,
    XgboostMlConfigComponent,
    CatBoostMlConfigComponent,
    KnNeighborsMlConfigComponent,
    ExtraTreesMlConfigComponent,
    NnTorchMlConfigComponent,
    ArimaMlConfigComponent,
    PreviewModelComparisionComponent,
    PredictionConfigComponent,
    SvmConfigComponent,
    GaussianProcessClassificationConfigComponent,
    MatchingModelsDialogComponent,
    CreateNewWorkflowTemplateComponent,
    LoadWorkflowTemplatesDialogComponent,
    DropColumnsConfigComponent,
    ParquetWidgetConfigComponent,
    RenameColumnsConfigComponent,
    DatatypeConversionConfigComponent,
    DataVisualizationComponent,
    ExcelWidgetConfigComponent,
    FilterSelectionConfigComponent,
    EditModelComponent,
    ImageDatasetSelectionWidgetComponent,
    ImageRegionPropertiesWidgetComponent,
    ImageSpatialWidgetComponent,
    TextWidgetConfigComponent
  ],

  imports: [
    // CommonModule,
    MatSlideToggleModule,
    SharedModule,
    ColorPickerModule,
    RouterModule.forChild(routes),
    PlotlyModule,
    MatPaginatorModule,
    ColorSketchModule
    // Add any other modules or dependencies specific to the Workflow Designer
  ],
  providers: [WorkflowService, AppendWidgetConfig],
})
export class WorkflowDesignerModule {}
