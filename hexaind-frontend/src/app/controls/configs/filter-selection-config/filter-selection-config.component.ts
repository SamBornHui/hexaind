import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { catchError, interval, of, Subscription, switchMap, takeWhile } from 'rxjs';
import { ApiService } from 'src/app/services/api.service';

@Component({
  selector: 'app-filter-selection-config',
  templateUrl: './filter-selection-config.component.html',
  styleUrls: ['./filter-selection-config.component.less']
})
export class FilterSelectionConfigComponent implements OnInit, OnDestroy {

  isCategorical: boolean = false;
  isNumerical: boolean = false;
  isDate: boolean = false;

  searchKeyword: string = "";
  columnName: string = "";
  CATEGORICAL: string = "CATEGORICAL";
  NUMERICAL: string = "NUMERICAL";

  datasetId: any;
  uniqueValues: any;
  filteredUniqueValues: any;
  selectedUniqueValues: string[] = [];
  uniqueValuesCount: number = 0;
  lastSelectedIndex: number | null = null;

  isLoading: boolean = false;
  isError: boolean = false;
  isChangeMade: boolean = false;

  POLLING_INTERVAL = 2000;
  uniqueValuesSubscription: Subscription | null = null;
  resultData: any;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private apiService: ApiService,
    public dialogRef: MatDialogRef<FilterSelectionConfigComponent>
  ) {
    if (data) {

      if (data.config) {
        this.searchKeyword = data.config.value;
        this.columnName = data.config.column_name;
        if (data.config.data_type === this.CATEGORICAL) {
          this.isCategorical = true;
        } else if (data.config.data_type === this.NUMERICAL) {
          this.isNumerical = true;
        } else {
          this.isDate = true;
        }
      }
      
      if (data.dataset_id) {
        this.datasetId = data.dataset_id;
      }
      
      if (this.datasetId && this.columnName !== "") {
        this.getUniqueValues();
      }
    }
  }

  ngOnInit(): void {
      
  }

  ngOnDestroy(): void {
    this.uniqueValuesSubscription?.unsubscribe();
  }

  clearKeyword() {
    this.searchKeyword = "";
    this.filterResults();
  }

  async getUniqueValues() {
    this.isLoading = true;
    this.apiService.getUniqueValuesOfColumn(this.datasetId,this.columnName).then(async response => {
      if (response) {
        if (response.api_job_id) {
          this.pollForUniqueValues();
        } else {      
          this.setUniqueValues(response);
          this.isLoading = false;  
        }
      } else {
        this.isLoading = false;
      }
    }).catch(error => {
      console.error('Error:', error);
      this.isLoading = false;
      this.isError = true;
    });
  }

  setUniqueValues(response: any) {
    this.uniqueValues = response.values;
    this.uniqueValuesCount = response.total
    this.uniqueValues = this.uniqueValues.map(
        (element: any) => {
          return {
            value: element,
            checked: false,
          };
        },
    );
    this.filterResults();
  }

  pollForUniqueValues() {
    this.uniqueValuesSubscription = interval(this.POLLING_INTERVAL) 
    .pipe(
      switchMap(() => this.apiService.getUniqueValuesOfColumn(this.datasetId,this.columnName)),
      takeWhile(response =>  response && response.api_job_id, true),
      catchError(error => {
        console.error('Error during polling:', error);
        this.uniqueValuesSubscription?.unsubscribe();
        this.isLoading = false;
        this.isError = true;
        return of(null);
      })
    )
    .subscribe(response => {
      if (response && response.values) {
        this.setUniqueValues(response);
        this.isLoading = false;  
        this.uniqueValuesSubscription?.unsubscribe();
      } else {
        this.isLoading = false;  
      }
    });
  }

  filterResults() {
    this.filteredUniqueValues = this.uniqueValues.filter((element: any) =>
      element.value.toLowerCase().includes(this.searchKeyword.toLowerCase())
    );
  }

  onValueSelected(currentIndex: number) {
    const currentItem = this.filteredUniqueValues[currentIndex];

    if (this.lastSelectedIndex !== null && this.lastSelectedIndex !== currentIndex) {
      this.filteredUniqueValues[this.lastSelectedIndex].checked = false;
    }

    // when multi selected is allowed, we will just append
    this.selectedUniqueValues = currentItem.checked ? [currentItem.value] : [];
    this.lastSelectedIndex = currentItem.checked ? currentIndex : null;
    this.isChangeMade = this.selectedUniqueValues.length > 0;
  }

  onSave() {
    this.resultData = { 
      "selected_values": this.selectedUniqueValues
    };
    this.closeDialog();
  }

  onClear() {
    if (this.lastSelectedIndex !== null) {
      this.filteredUniqueValues[this.lastSelectedIndex].checked = false;
    }

    this.isChangeMade = false;
  }

  closeDialog() {
    this.dialogRef.close(this.resultData); 
  }
}
