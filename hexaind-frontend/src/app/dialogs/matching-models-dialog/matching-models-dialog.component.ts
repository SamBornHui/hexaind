import { Component, Inject, Output } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DataService } from '../../pages/data/services/data.service';
import { Subject } from 'rxjs';
import { ModelsService } from '../../pages/models/services/models.service';
import { ConfigService } from '../../pages/workflow-designer/workflow-canvas.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

interface ModelConfig {
  problem_type: string;
}

@Component({
  selector: 'app-matching-models-dialog',
  templateUrl: './matching-models-dialog.component.html',
  styleUrls: ['./matching-models-dialog.component.less'],
})
export class MatchingModelsDialogComponent {
  private searchTerms = new Subject<string>();
  searchText: string = '';
  dataSource: any;
  project_id: string | undefined = '';
  site_id: string = '1';

  displayedColumns: string[] = [
    'name',
    'type',
    'problem_type',
    'input',
    'output',
    'created_by',
    'created_at',
    'ml_deployed_status',
  ];
  selectedRow: any;

  constructor(
    private modelsService: ModelsService,
    private configService: ConfigService,
    private errorHandlerService: ErrorHandlerService,
    public dialogRef: MatDialogRef<MatchingModelsDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) { }

  ngOnInit() {
    this.project_id = this.configService.SelectedProjectId;
    this.getMatchingModels();
  }

  async getMatchingModels() {
    try {
      this.dataSource = await this.modelsService.getMatchingModels(
        this.site_id,
        this.project_id as string,
        {
          input_cols: this.data.input_cols
        }
      );
      if (this.data.flag === true) {
        this.dataSource = this.dataSource.filter((value: { model: { configs: { output_cols: any[]; }; }; }) => {
          return this.data.output_cols.some((col: any) => value.model.configs.output_cols.includes(col));
        });
      }

      this.dataSource.forEach((item: any, index: number) => {
        if (!('problem_type' in item.model.configs)) {
          (this.dataSource[index]['model']['configs'] as ModelConfig)[
            'problem_type'
          ] = 'regression';
        }
      });

      this.sortLastModified();
    } catch (error) {
      console.error('Error fetching models:', error);
      this.errorHandlerService.handleError(error);
    }
  }
  sortLastModified(): void {
    this.dataSource.sort((a: any, b: any) => {
      const dateA = new Date(a['created_at']).getTime();
      const dateB = new Date(b['created_at']).getTime();
      return dateB - dateA;
    });
  }
  onRadioChange(row: any) {
    this.selectedRow = row;
  }

  onSubmit() {
    this.dialogRef.close({ success: true, model: this.selectedRow });
  }
}
