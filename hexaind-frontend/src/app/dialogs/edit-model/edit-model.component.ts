import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { ModelsService } from 'src/app/pages/models/services/models.service';
import { ConfigService } from 'src/app/services/config.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

@Component({
  selector: 'app-edit-model',
  templateUrl: './edit-model.component.html',
  styleUrls: ['./edit-model.component.less']
})
export class EditModelComponent {
  model_name: string = "";
  project_id: string | undefined;
  site_id: string | undefined = '1';
  modelDetails: any

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<EditModelComponent>,
    private toaster: ToastrService,
    private configService: ConfigService,
    private modelsService: ModelsService,
    public errorHandlerService: ErrorHandlerService,
  ) {
    this.project_id = this.configService.SelectedProjectId;
    this.modelDetails = this.data.model_object;
  }

  ngOnInit() {
    this.model_name = this.modelDetails.model.name;
  }

  async updateTheModelObject() {
    try {
      this.modelDetails.model.name = this.model_name;
      const saveResult = await this.modelsService.updateModel(
        this.site_id ?? '',
        this.project_id,
        [this.modelDetails],
      );
      if (saveResult?.length === 0) {
        this.toaster.success('Model name updated successfully');
      } else {
        this.toaster.error('Model with this name already exists');
      }
      this.close();
    } catch (error) {
      console.error('Error while saving the model:', error);
      this.errorHandlerService.handleError(error);
    }
  }

  close() {
    this.dialogRef.close({ success: false });
  }
}
