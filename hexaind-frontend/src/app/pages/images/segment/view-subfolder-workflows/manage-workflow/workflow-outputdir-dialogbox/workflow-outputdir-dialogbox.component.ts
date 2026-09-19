import { Component, OnInit, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import clone from 'clone';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';

export interface DialogData {
  name: string;
}

@Component({
  selector: 'app-workflow-outputdir-dialogbox',
  templateUrl: './workflow-outputdir-dialogbox.component.html',
  styleUrls: ['./workflow-outputdir-dialogbox.component.less'],
})
export class WorkflowOutputdirDialogboxComponent implements OnInit {
  currentUser: any = {};
  outputDirOptions: any = {};

  constructor(
    public imageAnalysisService: ImageAnalysisService,
    private toastr: ToastrService,
    public dialogRef: MatDialogRef<WorkflowOutputdirDialogboxComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {
    dialogRef.disableClose = true;
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.outputDirOptions = clone(this.data['outputDirOptions']);
  }

  checkOutDirectory() {
    if (this.outputDirOptions['defaultDirectory']) {
      this.outputDirOptions['setDirectory'] = true;
      this.outputDirOptions['outputDirectory'] = '';
      this.dialogRef.close({ outputDirOptions: this.outputDirOptions });
    } else {
      if (this.outputDirOptions['outputDirectory'] != '') {
        let reqData = {
          outputDirectory: this.outputDirOptions['outputDirectory'],
        };
        this.imageAnalysisService
          .checkOutputDirectory(reqData)
          .then((response) => {
            if (response['directory_exist']) {
              this.outputDirOptions['setDirectory'] = true;
              this.dialogRef.close({ outputDirOptions: this.outputDirOptions });
            }
          })
          .catch((error) => {
            console.error('Error fetching mounted drive data:', error);
          });
      } else {
        this.toastr.error('Failed to get directory information', '', {
          positionClass: 'custom-toast-position',
        });
      }
    }
  }
  closeDialog(_flag: boolean) {
    this.dialogRef.close();
  }
}
