import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { JupyterNotebookService } from '../../pages/jupyter-notebooks/services/jupyter-notebook.service';
import { ConfigService } from '../../services/config.service';

@Component({
  selector: 'app-create-jupyter-notebook',
  templateUrl: './create-jupyter-notebook.component.html',
  styleUrls: ['./create-jupyter-notebook.component.less']
})
export class CreateJupyterNotebookComponent {
  JNB_name: string = '';
  JNB_description: string = '';
  updateButton: boolean = true;
  currentUserId: string | undefined;
  constructor(
    public dialogRef: MatDialogRef<CreateJupyterNotebookComponent>,
    public toaster: ToastrService,
    public JupyterNotebookService: JupyterNotebookService,
    public configService: ConfigService,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {
    this.currentUserId = JSON.parse(localStorage.getItem('currentUser')!)['_id'];
  }

  ngOnInit() { }

  onClosePanel() {
    this.dialogRef.close();
  }

  async createJupyterNotebook() {
    if (this.data.type == 'MASTER' || this.data.type == 'CLONE') {
      if (this.JNB_name == '') {
        this.toaster.error('Please enter a name for the Jupyter Notebook');
        return;
      } else {
        var source = this.data.notebook.relative_path;
        var destination;

        if (this.data.type == 'MASTER') {
          const basePath = source.split('/')[0];
          destination = `${basePath}/u_${this.currentUserId}/${this.JNB_name}`;
        } else if (this.data.type == 'CLONE') {
          const basePath = source.split('/')[0];
          destination = `${basePath}/master_notebooks/${this.JNB_name}`;
        }
        if (source && destination) {
          const response = await this.JupyterNotebookService.createJupyterNotebook(source, destination, this.configService.SelectedProjectId || '');
          if (response.status === true) {
            this.dialogRef.close(true);
          } else {
            this.toaster.error('Failed to create Jupyter Notebook');
          }
        }
      }
    } else if(this.data.type == 'create') {
      if (this.JNB_name == '') {
        this.toaster.error('Please enter a name for the Jupyter Notebook');
        return;
      }
      if (this.JNB_description == '') {
        this.toaster.error('Please enter a description for the Jupyter Notebook');
        return;
      }

      if (this.JNB_name && this.JNB_description) {
        const response = await this.JupyterNotebookService.createNewJupyterNotebook(this.JNB_name, this.JNB_description, this.configService.SelectedProjectId || '');
        if (response.status === true) {
          this.dialogRef.close(true);
        } else {
          this.toaster.error('Failed to create Jupyter Notebook');
        }
      }
    }
  }
}
