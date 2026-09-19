import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { DataPreviewService } from '../services/data-preview.service'

@Component({
  selector: 'app-metadata',
  templateUrl: './metadata.component.html',
  styleUrls: ['./metadata.component.less']
})
export class MetadataComponent implements OnChanges {
  @Input() dataset_id!: string;

  isGeneralInfoExpanded: boolean = true;
  isDatasetHistoryExpanded: boolean = true;
  isCurationHistoryExpanded: boolean = true;
  generalData: any
  datasetHistory = [];
  datasetHistorycolumns: string[] = ['user', 'action', 'date'];
  curationHistory = [];

  constructor(private dataPreviewService: DataPreviewService) { }

  ngOnInit() {
    
  }

  getDataPreview() {
    this.dataPreviewService.getMetadata(this.dataset_id).then(async response => {
      if (response) {
        this.generalData = response;
      }
    }).catch(error => {
      console.error('Error:', error);
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataset_id']) {
      const previousValue = changes['dataset_id'].previousValue;
      const currentValue = changes['dataset_id'].currentValue;

      if (previousValue!==currentValue) {
        this.getDataPreview();
      }
    }
  }

  toggleTable(type: any) {
    if (type === "general") {
      this.isGeneralInfoExpanded = !this.isGeneralInfoExpanded;
    }
    if (type === "dataset-history") {
      this.isDatasetHistoryExpanded = !this.isDatasetHistoryExpanded;
    }
    if (type === "curation-history") {
      this.isCurationHistoryExpanded = !this.isCurationHistoryExpanded;
    }
  }
}
