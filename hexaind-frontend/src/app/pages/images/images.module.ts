// images.module.ts
import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared.module';
import { RouterModule, Routes } from '@angular/router';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

import { ImageDetailsComponent } from 'src/app/pages/images/details/details.component';
import { ImagesComponent } from 'src/app/pages/images/images.component';
import { ImageCleanupComponent } from 'src/app/pages/images/cleanup/cleanup.component';
import { ImageSegmentComponent } from 'src/app/pages/images/segment/segment.component';
import { ImageAnnotateComponent } from 'src/app/pages/images/annotate/annotate.component';
import { ImageLeftNavComponent } from 'src/app/pages/images/image-left-nav/image-left-nav.component';
// import { ImagesPreviewComponent } from 'src/app/pages/images/preview/preview.component';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';


import { ViewSubfolderWorkflowsComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/view-subfolder-workflows.component';
import { ViewImagesAndWorkflowsComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/view-images-and-workflows/view-images-and-workflows.component';
import { ImagesGridComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/view-images-and-workflows/images-grid/images-grid.component';
import { WorkflowsGridComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/view-images-and-workflows/workflows-grid/workflows-grid.component';

import { ViewFullImageDialogBox } from 'src/app/pages/images/segment/view-image-dialog-box/view-full-image-dialog-box.component';
import { ImageAnalysisDialogBoxComponent } from 'src/app/pages/images/segment/image-analysis-dialog-box/image-analysis-dialog-box.component';
import { ManageWorkflowComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/manage-workflow/manage-workflow.component';
import { SaveWorkflowDialogBox } from 'src/app/pages/images/segment/view-subfolder-workflows/manage-workflow/save-workflow-dialogbox/save-workflow-dialogbox.component';
import { SaveWorkflowConfirmationDialogboxComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/manage-workflow/save-workflow-confirmation-dialogbox/save-workflow-confirmation-dialogbox.component';
import { SaveAnalysisConfirmationDialogComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/manage-workflow/save-analysis-confirmation-dialog/save-analysis-confirmation-dialog.component';
import { DragulaModule } from 'ng2-dragula';
import { NgxImageZoomModule } from 'ngx-image-zoom';
import { WorkflowOutputdirDialogboxComponent } from 'src/app/pages/images/segment/view-subfolder-workflows/manage-workflow/workflow-outputdir-dialogbox/workflow-outputdir-dialogbox.component';

import { ApplyWorkflowsDialogboxComponent } from './segment/view-subfolder-workflows/view-images-and-workflows/apply-workflows-dialogbox/apply-workflows-dialogbox.component';
// import { NouisliderModule } from 'ng2-nouislider';
import { ImageCropperModule } from 'ngx-image-cropper';
import { ViewCleanFullImageDialogBox } from 'src/app/pages/images/cleanup/view-cleanup-image-dialog-box/view-cleanup-image-dialog-box.component'


const routes: Routes = [
  {
    path: '',
    component: ImagesComponent,
  },
];

@NgModule({
  declarations: [
    ImagesComponent,
    ImageDetailsComponent,
    ImageCleanupComponent,
    ImageAnnotateComponent,
    ImageSegmentComponent,
    ManageWorkflowComponent,
    ImageLeftNavComponent,
    ViewSubfolderWorkflowsComponent,
    ViewFullImageDialogBox,
    ImageAnalysisDialogBoxComponent,
    ViewImagesAndWorkflowsComponent,
    ImagesGridComponent,
    WorkflowsGridComponent,
    SaveWorkflowDialogBox,
    SaveWorkflowConfirmationDialogboxComponent,
    SaveAnalysisConfirmationDialogComponent,
    WorkflowOutputdirDialogboxComponent,
    ApplyWorkflowsDialogboxComponent,
    ViewCleanFullImageDialogBox
  ],

  imports: [
    SharedModule,
    RouterModule.forChild(routes),
    DragulaModule.forRoot(),
    NgxImageZoomModule,
    ImageCropperModule
  ],
  providers: [],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class ImagesModule { }
