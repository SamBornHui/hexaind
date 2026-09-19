import { WeekDay } from '@angular/common';
import { Component, EventEmitter, Inject, Input, Optional, Output, TemplateRef, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { debounceTime, Subject } from 'rxjs';
import { WidgetType } from 'src/app/models/workflow-models';



@Component({
  selector: 'app-column-drop-down',
  templateUrl: './column-drop-down.component.html',
  styleUrls: ['./column-drop-down.component.less']
})
export class ColumnDropDownComponent {
  columnsFilterWord: any;
  isAllColumnsChecked: any;
  columnsList: any
  columnsDataSource: any;
  selectedColumnsFilterWord:any;
  isAllSelectedColumnsChecked:any;
  selectedColumnsList:any
  selectedColumnsDataSource:any
  changeMade: boolean = false
  selectedParameterForConfiguration: any
  showDropDownConfig: boolean = false
  filterSubject = new Subject<string>()
  selectedColumnFilterSubject = new Subject<string>()
  infoRegardingTheColumns : any
  isSaveDisabled = true
  widgetType: WidgetType;
  datatypeOptions = [
    "INTEGER",
    "FLOAT",
    "STRING",
    "DATE",
    "DATETIME"
  ];

  @ViewChild('defaultTemplateUnSelectedList') defaultTemplateUnSelectedListTemplate! : TemplateRef<any>;
  @ViewChild('defaultTemplateSelectedList') defaultTemplateSelectedListTemplate! : TemplateRef<any>;
  @ViewChild('renameColumnUnselectedList') renameColumnUnselectedListTemplate! : TemplateRef<any>;
  @ViewChild('renameColumnSelectedList') renameColumnSelectedListTemplate! : TemplateRef<any>;
  @ViewChild('dataTypeConversionUnselectedList') dataTypeConversionUnselectedListTemplate! : TemplateRef<any>;
  @ViewChild('dataTypeConversionSelectedList') dataTypeConversionSelectedListTemplate! : TemplateRef<any>;



  constructor(private dialogRef: MatDialogRef<ColumnDropDownComponent>,
    @Inject(MAT_DIALOG_DATA) public dialogData:any) {

      
    this.infoRegardingTheColumns = this.dialogData.infoRegardingTheColumns || "";
    this.columnsList = this.dialogData.columnsList
    this.selectedColumnsList = this.dialogData.selectedColumnsList
    this.widgetType = this.dialogData.widgetType
  }

  ngOnInit() {

    this.columnsDataSource = this.columnsList
    this.selectedColumnsDataSource = this.selectedColumnsList

    this.filterSubject.pipe(
      debounceTime(1000),
    ).subscribe(filterText => {
      this.resetCheckedInColumnList()
      this.isAllColumnsChecked = false;
      this.columnsDataSource = this.columnsDataSource.filter((item: any) => item.name.toLowerCase().includes(this.columnsFilterWord.toLowerCase()));
    })

    this.selectedColumnFilterSubject.pipe(
      debounceTime(1000), 
    ).subscribe(filterText => {
      this.resetCheckedInSelectedColumnsList();
      this.isAllSelectedColumnsChecked = false;
      this.selectedColumnsDataSource = this.selectedColumnsDataSource.filter((item: any) => item.name.toLowerCase().includes(this.selectedColumnsFilterWord.toLowerCase()));
    })
  }

  getTemplateForUnSelectedList() {
    switch(this.widgetType) {
      case WidgetType.RENAME_COLUMNS:
        return this.renameColumnUnselectedListTemplate
      case WidgetType.DATATYPE_CONVERSION:
        return this.dataTypeConversionUnselectedListTemplate
    }
    return this.defaultTemplateUnSelectedListTemplate
    
  }
  
  getTemplateForSelectedList() {
    switch(this.widgetType) {
      case WidgetType.RENAME_COLUMNS:
        return this.renameColumnSelectedListTemplate
      case WidgetType.DATATYPE_CONVERSION:
        return this.dataTypeConversionSelectedListTemplate
    }
    return this.defaultTemplateSelectedListTemplate
  }


  
  applyFilterOnColumns() {
    this.filterSubject.next(this.columnsFilterWord)
  }

  resetCheckedInColumnList() {
    this.columnsList = this.columnsList.map((column:any) => ({
      ...column,
      checked: false
    }))
    this.columnsDataSource = this.columnsList;
  }

  toggleAllColumns(event: any) {
    const checked = event.checked;
    this.columnsDataSource.forEach((element:any) => {
      element.checked = checked
    })
    // this.columnsList.forEach((element:any)=> {
    //   if(filteredColumnsList.some((filteredElement:any) => filteredElement.name === element.name)) {
    //     element.checked = checked
    //   }
    // })
  }

  onColumnClicked() {
    this.checkIfAllColumnsChecked();
  }
  checkIfAllColumnsChecked() {
    this.isAllColumnsChecked = this.columnsList.every((element: any) => element.checked);
  }


  onSelectColumns() {
    this.isSaveDisabled = false
    const columnsMovedFromUnSelectedToSelectedList = this.logicForMovingDataFromUnselectedToSelect()
    this.selectedColumnsList = [
      ...this.selectedColumnsList,
      ...columnsMovedFromUnSelectedToSelectedList,
    ];
    this.columnsList = this.columnsList.filter(
      (column: any) => !column.checked,
    );
    this.selectedColumnsDataSource = this.selectedColumnsList,

    this.columnsDataSource = this.columnsList;

    if (columnsMovedFromUnSelectedToSelectedList.length > 0) this.changeMade = true;
    this.isAllColumnsChecked = false;
    this.columnsFilterWord = '';
  }

  onUnselectColumns() {
    this.isSaveDisabled = false
    const columnsMovedFromSelectedToUnselectedList = this.logicForMovingDataFromSelectedToUnSelect();
    this.columnsList = [...this.columnsList, ...columnsMovedFromSelectedToUnselectedList];
    this.selectedColumnsList = this.selectedColumnsList.filter(
      (column: any) => !column.checked,
    );
    this.selectedColumnsDataSource = this.selectedColumnsList,
    this.columnsDataSource = this.columnsList;

    if (columnsMovedFromSelectedToUnselectedList.length > 0) this.changeMade = true;
    this.isAllSelectedColumnsChecked = false;
    this.selectedColumnsFilterWord = '';
  }

  logicForMovingDataFromUnselectedToSelect() {
    if (this.dialogData.logicForMovingDataFromUnselectedToSelect) {
      return this.dialogData.logicForMovingDataFromUnselectedToSelect(this.columnsList)
    }

    return this.columnsList
    .filter((column: any) => column.checked)
    .map((column: any) => ({
      ...column,
      checked: false,
    }));

  }

  logicForMovingDataFromSelectedToUnSelect() {

    if(this.dialogData.logicForMovingDataFromSelectedToUnSelect) {
      return this.dialogData.logicForMovingDataFromSelectedToUnSelect(this.selectedColumnsList) 
    }

    return this.selectedColumnsList
      .filter((column: any) => column.checked)
      .map((column: any) => ({
        ...column,
        checked: false,
      }));
  }


  applyFilterOnSelectedColumns() {
    this.selectedColumnFilterSubject.next(this.selectedColumnsFilterWord)
  }


  resetCheckedInSelectedColumnsList() {
    this.selectedColumnsList = this.selectedColumnsList.map((column: any) => ({
      ...column, 
      checked: false 
    }));
    this.selectedColumnsDataSource = this.selectedColumnsList;
  }

  toggleAllSelectedColumns(event: any) {
    const checked = event.checked;
    this.selectedColumnsDataSource.forEach((element: any) => {
      element.checked = checked
    })
    // const filteredSelectedColumnsList = this.selectedColumnsDataSource.slice();
    // this.selectedColumnsList.forEach((element: any) => {
    //   if (filteredSelectedColumnsList.some((filteredElement: any) => filteredElement.name === element.name)) {
    //     element.checked = checked; 
    //   }
    // });
  }

  onSelectedColumnClicked() {
    this.checkIfAllSelectedColumnsChecked();
  }

  checkIfAllSelectedColumnsChecked() {
    this.isAllSelectedColumnsChecked = this.selectedColumnsList.every((element: any) => element.checked);
  }

  saveTheColumns() {
    this.unCheckEveryElement()
    this.dialogRef.close({
      columnsList: this.columnsList,
      selectedColumnList: this.selectedColumnsList,
      isSaved: true
    })
  }

  closeWithoutSaving() {
    this.unCheckEveryElement()
    this.dialogRef.close({isSaved: false})
  }

  unCheckEveryElement() {
    this.columnsList.forEach((element:any) => {
      element.checked = false
    })
    this.selectedColumnsList.forEach((element:any) => {
      element.checked = false
    })
  }


}
