import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NewConnectorService } from '../connector-dialog/services/new-connector.service';

@Component({
  selector: 'app-big-query-result-preview',
  templateUrl: './big-query-result-preview.component.html',
  styleUrls: ['./big-query-result-preview.component.less']
})
export class BigQueryResultPreviewComponent {

  result: any;
  displayedColumns: any;
  dataSource: any;
  tableData:  boolean | undefined;
  title: string ='Big Query Preview';
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<BigQueryResultPreviewComponent>,
    private connectorService: NewConnectorService,
  ) {}
  close(): void {
    this.dialogRef.close();
  }
  ngOnInit() {
    this.title = this.data.title;
    this.result = this.data.result;
    this.displayedColumns = this.result.columns;
    this.dataSource = this.result.data;
    this.tableData = this.data.tableData;
    console.log("the result columns is :",this.result);
  }
}
