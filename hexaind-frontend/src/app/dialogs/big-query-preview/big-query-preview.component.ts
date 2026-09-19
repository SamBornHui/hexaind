import { Component } from "@angular/core";
import { MatDialogRef } from "@angular/material/dialog";

@Component({
  selector: "app-big-query-preview",
  templateUrl: "./big-query-preview.component.html",
  styleUrls: ["./big-query-preview.component.less"],
})
export class BigQueryPreviewComponent {
  isNumericalExpanded: boolean = true;
  isCategoricalExpanded: boolean = true;
  isGeneralInfoExpanded: boolean = true;
  isDatasetHistoryExpanded: boolean = true;
  isCurationHistoryExpanded: boolean = true;
  columns: string[] = ['column1', 'column2', 'mean', 'median', 'std', 'missingValues', 'count'];
  columnsB: string[] = ['column1', 'column2', 'unique', 'top', 'freq', 'missingValues', 'count'];
  columnsC: string[] = ['rowNo', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8'];

  tableData = [
    { column1: "Value 1A", column2: "Value 1B" },
    { column1: "Value 2A", column2: "Value 2B" },
  ];

  datasetHistory = [];
  datasetHistorycolumns: string[] = ['user', 'action', 'date'];
  curationHistory = [];
  formatLabel(value: number): string {
    console.log(value);
    
    return `${value}`;
  }

  constructor(public dialogRef: MatDialogRef<BigQueryPreviewComponent>) {}

  close(): void {
    this.dialogRef.close();
  }

  toggleTable(type: any) {
    if (type === "numerical") {
      this.isNumericalExpanded = !this.isNumericalExpanded;
    }
    if (type === "categorical") {
      this.isCategoricalExpanded = !this.isCategoricalExpanded;
    }
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
