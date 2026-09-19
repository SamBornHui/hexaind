import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { SelectionModel } from '@angular/cdk/collections';

@Component({
  selector: 'app-injestion-dialog',
  templateUrl: './injestion-dialog.component.html',
  styleUrls: ['./injestion-dialog.component.less']
})
export class InjestionDialogComponent {
[x: string]: any;
  currentStep = 1
  totalSteps = 3
  dataSource: any = []
  selection: any = []
  columnsData = [
    {
      column_no: 1,
      column_name: 'CRIM',
      data_type: 'Numerical'
    },
    {
      column_no: 2,
      column_name: 'ZN',
      data_type: 'Numerical'
    },
    {
      column_no: 3,
      column_name: 'INDUS',
      data_type: 'Numerical'
    },
    {
      column_no: 4,
      column_name: 'CHAS',
      data_type: 'Numerical'
    },
    {
      column_no: 5,
      column_name: 'NOX',
      data_type: 'Numerical'
    },
    {
      column_no: 6,
      column_name: 'RM',
      data_type: 'Numerical'
    },
    {
      column_no: 7,
      column_name: 'AGE',
      data_type: 'Numerical'
    },
    {
      column_no: 8,
      column_name: 'DIS',
      data_type: 'Numerical'
    }
  ]
  previewDataSource: any = []
  previewColumnsData = [
    {
      row_no: 1,
      CRIM: 'value',
      ZN: 'value',
      INDUS: 'value',
      CHAS: 'value',
      NOX: 'value',
      RM: 'value',
      AGE: 'value',
      DIS: 'value',
    },
    {
      row_no: 2,
      CRIM: 'value',
      ZN: 'value',
      INDUS: 'value',
      CHAS: 'value',
      NOX: 'value',
      RM: 'value',
      AGE: 'value',
      DIS: 'value',
    },
    {
      row_no: 3,
      CRIM: 'value',
      ZN: 'value',
      INDUS: 'value',
      CHAS: 'value',
      NOX: 'value',
      RM: 'value',
      AGE: 'value',
      DIS: 'value',
    },
    {
      row_no: 4,
      CRIM: 'value',
      ZN: 'value',
      INDUS: 'value',
      CHAS: 'value',
      NOX: 'value',
      RM: 'value',
      AGE: 'value',
      DIS: 'value',
    },
    {
      row_no: 5,
      CRIM: 'value',
      ZN: 'value',
      INDUS: 'value',
      CHAS: 'value',
      NOX: 'value',
      RM: 'value',
      AGE: 'value',
      DIS: 'value',
    },
    {
      row_no: 6,
      CRIM: 'value',
      ZN: 'value',
      INDUS: 'value',
      CHAS: 'value',
      NOX: 'value',
      RM: 'value',
      AGE: 'value',
      DIS: 'value',
    },
  ]
  displayedColumns: string[] = ['select', 'column_no', 'column_name', 'data_type'];
  previewDisplayedColumns: string[] = ['row_no', 'CRIM', 'ZN', 'INDUS', 'CHAS', 'NOX', 'RM', 'AGE', 'DIS'];
  
  constructor() { }

  ngOnInit() {
    this.dataSource = new MatTableDataSource(this.columnsData);
    this.selection = new SelectionModel(true, []);
    this.previewDataSource = new MatTableDataSource(this.previewColumnsData);

  }

  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }

  masterToggle() {
    if (this.isAllSelected()) {
      this.selection.clear();
    } else {
      this.dataSource.data.forEach((row: any) => this.selection.select(row));
    }
  }

  onSearchTextChange(event: any){

  }

  next() {
    this.currentStep = this.currentStep + 1
  }

  previous() {
    this.currentStep = this.currentStep - 1
  }

  finish() {

  }
}
