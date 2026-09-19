import {
  Component,
  Output,
  EventEmitter,
  Inject,
  OnInit,
  ViewChild,
} from '@angular/core';
import { Project } from 'src/app/models/project-models';
import { ApiService } from 'src/app/services/api.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DataService } from 'src/app/pages/data/services/data.service';
import { NotificationComponent } from 'src/app/controls/notification/notification.component';

@Component({
  selector: 'app-update-datasets',
  templateUrl: './update-datasets.component.html',
  styleUrls: ['./update-datasets.component.less'],
})
export class UpdateDatasetsComponent {
  @Output() closePanelClicked = new EventEmitter<any>();
  @Output() projectCreatedEvent = new EventEmitter<Project>();
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  newDatasetName: string = '';
  datasetNameError: string = '';
  datasetNameExistsError: string = '';
  updateButton: any;
  projects: any = [];

  isCreatingProject: boolean = false;
  emptyName: boolean = false;
  constructor(
    private dialogRef: MatDialogRef<UpdateDatasetsComponent>,
    private dataService: DataService,
    @Inject(MAT_DIALOG_DATA)
    public data: {
      name: string;
      datasetId: string;
    }, // Inject the project data
    private apiService: ApiService,
  ) {}

  ngOnInit(): void {
    if (this.data) {
      this.newDatasetName = this.data['name'];
    }
  }

  onClosePanel() {
    this.closePanelClicked.emit();
  }

  async onUpdateDatasets() {
    console.log(this.newDatasetName);
    let obj: { name: string; dataset_id: string } = {
      name: '',
      dataset_id: '',
    };
    if (this.newDatasetName) {
      this.emptyName = false;
      obj['name'] = this.newDatasetName;
      obj['dataset_id'] = this.data['datasetId'];
      this.dataService.renameDataset(obj).subscribe(
        (res) => {
          if (res['status']) {
            this.dialogRef.close(res);
          }
        },
        (error) => {
          // Handle HTTP request error
          console.error('An error occurred:', error);
        },
      );
    } else {
      this.emptyName = true;
      return;
    }
  }
}
