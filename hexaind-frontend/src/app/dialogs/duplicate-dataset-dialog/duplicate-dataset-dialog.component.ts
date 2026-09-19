import { Component, Inject } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ApiService } from '../../services/api.service';
import { MatTreeNestedDataSource } from '@angular/material/tree';
import { NestedTreeControl } from '@angular/cdk/tree';
import { SelectionModel } from '@angular/cdk/collections';
import { FileStructureNodeResponse } from 'src/app/models/api-models';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-duplicate-dataset-dialog',
  templateUrl: './duplicate-dataset-dialog.component.html',
  styleUrls: ['./duplicate-dataset-dialog.component.less'],
})
export class DuplicateDatasetDialogComponent {
  treeControl = new NestedTreeControl<FileStructureNodeResponse>(
    (node) => node.children,
  );
  dataSource = new MatTreeNestedDataSource<FileStructureNodeResponse>();
  selection = new SelectionModel<FileStructureNodeResponse>(false);
  files: any = [];
  path: any;
  permittedExtensions: string = "";
  folderService:any;
  dataset_name:string="";
  currentUser:any;
  hasChild = (_: number, node: FileStructureNodeResponse) =>
    !!node.children && node.children.length > 0;


  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<DuplicateDatasetDialogComponent>,
    private apiService: ApiService,
    public dialog: MatDialog,
    private toaster:ToastrService
  ) {
    this.folderService = this.data.dataService;
  }

  ngOnInit() {
    console.log(this.data)
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);

    this.files = this.data.treeData;
    this.dataSource.data = this.files;
    this.treeControl.dataNodes = this.dataSource.data;
    this.treeControl.expandAll();
  }

  toggleFileSelection(node: any) {
    this.selection.toggle(node);
    if (node.type === 'file') {
      this.path = node.full_path;
    } else if (node.type === 'folder') {
      this.path = node.full_path;
    }
  }

  isFileSelected(node: FileStructureNodeResponse) {
    return this.selection.isSelected(node);
  }

  getSelectedNode(): FileStructureNodeResponse | null {
    return this.selection.selected.length ? this.selection.selected[0] : null;
  }

  async onDuplicate(){
    const selectedNode = this.getSelectedNode();
    let duplicateInfo:any = {
      "user_id": this.currentUser._id,
      "datasetId": this.data.element._id,
      "datasetName": this.dataset_name,
      "folderPath": "",
      "type":(this.data.element.dataset_type.toLowerCase()=='python')?'module':'dataset'
    }
    if (selectedNode) {
      duplicateInfo["folderPath"] = selectedNode.full_path;
    }
    this.folderService
        .duplicateDataset(duplicateInfo)
        .then((response:any) => {
          if (response) {
            this.toaster.success('Duplicate dataset created successfully', '',{
              positionClass: 'custom-toast-position'
            });
            this.dialogRef.close({success:true});
          }
        })
        .catch((error:any) => {
          console.error('Error moving dataset:', error);
        });
  }
  filterNodes(event: Event) {
    const filterText = (event.target as HTMLInputElement)?.value;
    if (!filterText) {
      this.dataSource.data = this.files;
      this.treeControl.expandAll();
    } else {
      this.dataSource.data = this.filterNode(this.files, filterText);
      this.treeControl.dataNodes = this.dataSource.data;
      this.treeControl.expandAll();
    }
  }
  filterNode(
    nodes: FileStructureNodeResponse[],
    filterText: string,
  ): FileStructureNodeResponse[] {
    const filteredNodes: FileStructureNodeResponse[] = [];

    nodes.forEach((node:any) => {
      const children = node.children
        ? this.filterNode(node.children, filterText)
        : [];

      if (
        node.name.toLowerCase().includes(filterText.toLowerCase()) ||
        children.length > 0
      ) {
        const newNode = { ...node, children };
        filteredNodes.push(newNode);
      }
    });

    return filteredNodes;
  }
  disableActionButton(){
    if(this.dataset_name !=''){
      return false;
    }else{
      return true;
    }
  }

}
