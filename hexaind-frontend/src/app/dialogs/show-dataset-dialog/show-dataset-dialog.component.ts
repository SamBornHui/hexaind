import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { DataService } from '../../pages/data/services/data.service';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';

@Component({
  selector: 'app-show-dataset-dialog',
  templateUrl: './show-dataset-dialog.component.html',
  styleUrls: ['./show-dataset-dialog.component.less'],
})
export class ShowDatasetDialogComponent {
  private searchTerms = new Subject<string>();
  searchText: string = '';
  dataSource: any;
  filterDataset: any = [];
  SearchTerm: string = '';
  displayedColumns: string[] = [
    'name',
    'type',
    'size',
    'uploader',
    'last_modified',
  ];
  selectedRow: any;

  constructor(
    private dataService: DataService,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ShowDatasetDialogComponent>,
  ) {
    this.searchTerms.pipe(debounceTime(300)).subscribe((term) => {
      this.dataSource.filter = term.trim().toLowerCase();
    });
  }

  ngOnInit() {
    this.getDatasets();
  }

  async getDatasets() {
    var datasets: any;
    if (this.data.type === 'csv') {
      datasets = await this.dataService.GetDatasets('hexaind_csv');
      if (datasets) {
        this.dataSource = datasets.datasets;
        this.filterDataset = datasets.datasets;
      }
    } else if (this.data.type === 'parquet') {
      datasets = await this.dataService.GetDatasets('hexaind_parquet');
      if (datasets) {
        this.dataSource = datasets.datasets;
        this.filterDataset = datasets.datasets;
      }
    } else if (this.data.type === 'excel') {
      var xlsxResults = await this.dataService.GetDatasets('hexaind_excel');
      var datasetXlsx = xlsxResults.datasets;
      var xlsData = await this.dataService.GetDatasetsforXls('xls');
      var datasetXls = xlsData.datasets;
      datasets = [...datasetXlsx, ...datasetXls];
      if (datasets) {
        this.dataSource = datasets;
        this.filterDataset = datasets;
      }
    } else if (this.data.type === 'text') {
      var textResults = await this.dataService.GetDatasets('hexaind_text');
      var datasetText = textResults.datasets;
      var texData = await this.dataService.GetDatasetsforTex('tex');
      var datasetTex = texData.datasets;
      datasets = [...datasetText, ...datasetTex];
      if (datasets) {
        this.dataSource = datasets;
        this.filterDataset = datasets;
      }
    }
  }

  onRadioChange(row: any) {
    console.log('Radio button selected', row);
    this.selectedRow = row;
  }

  onSubmit() {
    this.dialogRef.close({ success: true, dataset: this.selectedRow });
  }

  searchDatasetNames(event: Event) {
    let result = [];
    if (this.SearchTerm) {
      result = this.filterDataset.filter((item: any) => {
        let datasetName = item.name.toLowerCase();
        let searchName = this.SearchTerm.toLowerCase();
        if (datasetName.includes(searchName)) {
          return datasetName.includes(searchName);
        } else {
          return false;
        }
      });
      this.dataSource = result;
    } else {
      this.dataSource = this.filterDataset;
    }
  }

  async sortData(sort: Sort) {
    this.filterDataset.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';

      if (sort.active === 'name') {
        aValue = a.name;
        bValue = b.name;
      } else if (sort.active === 'type') {
        aValue = a.dataset_type;
        bValue = b.dataset_type;
      } else if (sort.active === 'size') {
        aValue = a.dataset_location[0].size;
        bValue = b.dataset_location[0].size;
      } else if (sort.active === 'uploader') {
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
      } else if (sort.active === 'last_modified') {
        aValue = new Date(a.dataset_location[0].last_modified_at);
        bValue = new Date(b.dataset_location[0].last_modified_at);
      } else {
        aValue = a[sort.active];
        bValue = b[sort.active];
      }

      const compareValues = (valueA: any, valueB: any) => {
        if (valueA == null && valueB == null) {
          return 0;
        }
        if (valueA == null) {
          return -1;
        }
        if (valueB == null) {
          return 1;
        }
        if (!isNaN(valueA) && !isNaN(valueB)) {
          return valueA - valueB;
        }
        const dateA = new Date(valueA);
        const dateB = new Date(valueB);
        if (!isNaN(dateA.getTime()) && !isNaN(dateB.getTime())) {
          return dateA.getTime() - dateB.getTime();
        }
        return String(valueA).localeCompare(String(valueB));
      };

      const comparisonResult = compareValues(aValue, bValue);
      return sort.direction === 'asc' ? comparisonResult : -comparisonResult;
    });
    this.dataSource = new MatTableDataSource<any>(this.filterDataset);
    // this.setDatasetTableData();
  }
}
