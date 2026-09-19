import { CdkVirtualScrollViewport } from '@angular/cdk/scrolling';
import { Component, ElementRef, Inject, QueryList, ViewChild, ViewChildren } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ColumnDropDownComponent } from 'src/app/util-components/column-drop-down/column-drop-down.component';
import { DataCatalogService } from '../../tools/data-catalog/data-catalog.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-sigma-common-test',
  templateUrl: './sigma-common-test.component.html',
  styleUrls: ['./sigma-common-test.component.less']
})
export class SigmaCommonTestComponent {
  rows: any[][] = [];
  sigmaCommanValues: any;
  previewText: string = '';
  commonStepIdsList: any
  isCommonIdsSelectAll: boolean[] = [];
  index:any;
  searchCommonIds: string = '';
  filteredCommonStepIds: any[] = [];
  selectedCommonStepIds: string[][] = [];
  initialCommonIds: string[][] = [];
  isSaveCommonIds: boolean = true;
  uc3CommonStepIds: any;
  isGenerateButtonDisabled: boolean = false; 
  
  constructor(
    public dialogRef: MatDialogRef<SigmaCommonTestComponent>,
    public dialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private dataCatService: DataCatalogService,
    public toaster: ToastrService,
  ) {}

  ngOnInit(): void{
    //this.commonStepIdsList = this.data.list
    
    this.index = this.data.row
    this.data.globalList[this.index]['common_test_ids']['selected_values'].forEach((id:any)=>{
      this.selectedCommonStepIds.push(id)
      this.rows.push(id)
    })
    this.previewText = JSON.stringify(this.selectedCommonStepIds);
    if(this.selectedCommonStepIds.length == 0)
      {
        this.addRow()
      }
    console.log(this.selectedCommonStepIds,"selected common step ifs");
    
  }

  generateRandomString(length: any) {
    const characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    const charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
  }

  generateHugeArray(length: any) {
    let randomStrings = [];
    for (let i = 0; i < length; i++) {
        randomStrings.push(this.generateRandomString(40));
    }
    return randomStrings
  }

  onClose() {
    this.dialogRef.close();
  }
  addRow() {
    this.rows.push([]);
    this.filteredCommonStepIds = this.commonStepIdsList
  }

  removeRow(event:any,index: number) {
    this.rows.splice(index, 1);
    this.selectedCommonStepIds.splice(index,1)
    this.updatePreview(index);
  }

  updatePreview(index:number) {
    this.isCommonIdsSelectAll = this.rows.map(row => {
      return this.commonStepIdsList.every((id:any) => row.includes(id));
    })
    let allStepsSelected = this.selectedCommonStepIds[index] ? this.filteredCommonStepIds.every((id: any) => this.selectedCommonStepIds[index].includes(id)) : false;
    this.isCommonIdsSelectAll[index] = allStepsSelected
    this.previewText = JSON.stringify(this.selectedCommonStepIds);
  }

  selectAll(event: any, rowIndex: number) {
    if(event.checked){
      this.selectedCommonStepIds[rowIndex] = this.filteredCommonStepIds.map((common:any)=> common)
    }
    else
    {
      this.selectedCommonStepIds[rowIndex] = []
    }
    this.updatePreview(rowIndex);
  }

  saveCommonIds(){
    this.dialogRef.close(JSON.parse(this.previewText));
  }

  filterCommonIds(index:number){
    if(this.searchCommonIds){
      let arr = this.commonStepIdsList.filter((row:any) => row.toLowerCase().includes(this.searchCommonIds.toLowerCase()))
      this.filteredCommonStepIds = this.commonStepIdsList.filter((row:any) => row.toLowerCase().includes(this.searchCommonIds.toLowerCase()))
    }
    else
    {
      this.filteredCommonStepIds = this.commonStepIdsList
    }
  }

  onReset(){
    this.selectedCommonStepIds = []
    this.previewText = ''
    this.rows = [];
    this.rows.push([])
    this.isSaveCommonIds = true;
  }

  selectCommonIds(){
    if(this.selectedCommonStepIds.length > 0){
      this.isSaveCommonIds = false;
    }
    else{
      this.isSaveCommonIds = true;
    }
  }

  openColumnDropDown(index:any) {

    let selectedColumnsList:any;
    if(this.selectedCommonStepIds[index]?.length > 0) {
      selectedColumnsList = this.selectedCommonStepIds[index].map((name: string) => ({ 
        name: name, 
        checked: false 
      }));
    }
    else {
      selectedColumnsList = []
    }


    const selectedSet = new Set(this.selectedCommonStepIds[index])

    let columnsList = this.commonStepIdsList.filter((name: any) => !selectedSet.has(name)).map((name: string) => ({ 
      name: name, 
      checked: false 
    }));



    const dialogRef = this.dialog.open(ColumnDropDownComponent, {
      width: '70vw',
      height: '90vh',
      data: {
        columnsList,
        selectedColumnsList,
        infoRegardingTheColumns:"This is UC3"
      },
    })

    dialogRef.afterClosed().subscribe((result:any) => {
      if(result.isSaved) {
        this.selectedCommonStepIds[index] = result.selectedColumnList.map((element:any)=>element.name)
        this.updatePreview(index)
      }
    })
  }

  OnGenerateCommonIds(){
    //console.log(this.data,"get file patha");return false;
    this.isGenerateButtonDisabled = true; 
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    this.dataCatService.getQueryUniques(this.data.filePath, 'COMMON_TEST_ID', pageDetails,{}, undefined, true).subscribe({
      next: (res: any) => {
        if (res.body['uniques']) {
          this.commonStepIdsList = res.body['uniques'];
          this.filteredCommonStepIds = this.commonStepIdsList;
          this.initialCommonIds = [...this.selectedCommonStepIds]
          
          
          console.log(this.commonStepIdsList,"common step ids");
          
        } else {
          this.toaster.error('No unique common test IDs found.');
          
        }
      },
      error: (err: any) => {
        this.toaster.error('Error in fetching common ids');
       
      }
    });
  }

}


