import { Component, Inject } from '@angular/core';
import { DataCatalogService } from '../../tools/data-catalog/data-catalog.service';
import { ToastrService } from 'ngx-toastr';
import { ConfigService } from '../../workflow-designer/workflow-canvas.service';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-uc3-probe-model-popup',
  templateUrl: './uc3-probe-model-popup.component.html',
  styleUrls: ['./uc3-probe-model-popup.component.less']
})
export class Uc3ProbeModelPopupComponent {
  upload_file_path: any;
  @Inject(MAT_DIALOG_DATA) public data: any;
  constructor(
    public dialogRef: MatDialogRef<Uc3ProbeModelPopupComponent>,
    private configService: ConfigService,
    public dialog: MatDialog,
    private dataCatService: DataCatalogService,
    public toaster: ToastrService,
  ){
    
  }
  availableColumns : any = [];

  selectedColumns: any[] = [];
  availableColumnsFilter: string = '';
  selectedColumnsFilter: string = '';
  isAllSelected: boolean = false;
  AvailableColumnsSelectAll: boolean = false;

  isColumnDisplay : boolean = false;


  columnsFilterWord: any;
  isAllColumnsChecked: boolean = false;
  isAllSelectedColumnsChecked: boolean = false;
  selectedColumnsFilterWord: any;
  columnsDataSource :  any;
  columnsList : any= [];

  // selectedColumnsDataSource: any[] = ['Name', 'Marks'];
  // selectedColumnsList : any = ['Name', 'Marks']
  UC3SaveModelPopupButton(){
    this.dialogRef.close({ success: true, selectedProbeColumns: this.filteredSelectedColumns, upload_file_path: this.upload_file_path });
  }

  browseFileInputClick(fileInput: HTMLInputElement) {
    fileInput.click();
  }

  onCSVFileSelected(event : any){
    let path;
    const formData = new FormData();
    let selectedFile = event.target.files[0];
    formData.append('file', selectedFile);
    let file = this.dataCatService.getUC3ProbeCSVFileData(formData).subscribe({
      next: async (res: any) => {
        path = res['columns_file_path'];
        this.upload_file_path = res['uploaded_file_path'];
        this.getUniquesColumns(path);
        //this.toaster.success('Data Uploaded Sucessfully');
        this.UC3SaveModelPopupButton();
      },
      error: (err: any) => {
        this.toaster.error('Error in fetching data');
      },
    });
  }

  getUniquesColumns(columnPath : any){
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    this.dataCatService.getQueryUniques(columnPath,'COLUMNS',pageDetails,).subscribe({
      next: async (res: any) => {
        this.columnsDataSource = res['body']['uniques'];

        this.isColumnDisplay = this.columnsDataSource ? true : false;
        this.availableColumns = this.columnsDataSource.map((name: any) => ({ name, selected: false }));
        this.toaster.success('Data Uploaded Sucessfully');
      },
      error: (err: any) => {
        this.toaster.error('Error in fetching data');
      },
    });
  }



  get filteredAvailableColumns() {
    return this.availableColumns.filter((column : any)=>
      column.name.toLowerCase().includes(this.availableColumnsFilter.toLowerCase())
    );
  }

  // Get filtered list of selected columns based on the search filter
  get filteredSelectedColumns() {
    return this.selectedColumns.filter(column =>
      column.name.toLowerCase().includes(this.selectedColumnsFilter.toLowerCase())
    );
  }

  // Move selected columns to the selectedColumns array
  onSelectColumns() {
    const selected = this.availableColumns.filter((col : any)  => col.selected);
    this.selectedColumns.push(...selected);
    this.selectedColumns = this.selectedColumns.filter((col : any) => col.selected = true);
    this.availableColumns = this.availableColumns.filter((col : any) => !col.selected);
    this.onSelectedValuesChange();
    //this.resetSelection(this.selectedColumns);  // Deselect columns in selected list
  }

  // Move selected columns back to the availableColumns array
  onUnselectColumns() {
    const unselected = this.selectedColumns.filter(col => col.selected);
    this.availableColumns.push(...unselected);
    this.selectedColumns = this.selectedColumns.filter(col => !col.selected);
    this.resetSelection(this.availableColumns);  // Deselect columns in available list
    this.onAvailableValuesChange();
  }

  // Reset selection after moving columns
  resetSelection(columns: any[]) {
    columns.forEach(col => col.selected = false);
  }

  onSelectedValuesChange() {
    let selectedLength = 0;
    this.filteredSelectedColumns.forEach((col : any) => {
      if(col.selected == true){
        selectedLength++;
        //this.isAllSelected = false;
      }
    });

    this.filteredSelectedColumns.length === selectedLength ? this.isAllSelected = true : this.isAllSelected = false;
  }

  onAvailableValuesChange() {
    let selectedLength = 0;
    this.filteredAvailableColumns.forEach((col : any) => {
      if(col.selected == true){
        selectedLength++;
        //this.isAllSelected = false;
      }
    });

    this.filteredAvailableColumns.length === selectedLength ? this.AvailableColumnsSelectAll = true : this.AvailableColumnsSelectAll = false;
  }
  // Toggle select all checkboxes in the selected columns list
  toggleSelectAll() {
    this.filteredSelectedColumns.forEach(col => col.selected = this.isAllSelected);
  }

  toggleAvialableSelectAll() {
    this.filteredAvailableColumns.forEach((col : any) => col.selected = this.AvailableColumnsSelectAll);
  }

}
