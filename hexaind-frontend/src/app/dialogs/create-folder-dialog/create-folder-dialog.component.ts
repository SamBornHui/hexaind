import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ApiService } from '../../services/api.service';
import { MatTreeNestedDataSource } from '@angular/material/tree';
import { NestedTreeControl } from '@angular/cdk/tree';
import { SelectionModel } from '@angular/cdk/collections';
import { FileStructureNodeResponse } from 'src/app/models/api-models';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-create-folder-dialog',
  templateUrl: './create-folder-dialog.component.html',
  styleUrls: ['./create-folder-dialog.component.less'],
})
export class CreateFolderDialogComponent {
  treeControl = new NestedTreeControl<FileStructureNodeResponse>(
    (node) => node.children,
  );
  dataSource = new MatTreeNestedDataSource<FileStructureNodeResponse>();
  selection = new SelectionModel<FileStructureNodeResponse>(false);
  files: any = [];
  path: any;
  folderService: any;
  new_folder_name: string = '';
  hasChild = (_: number, node: FileStructureNodeResponse) =>
    !!node.children && node.children.length > 0;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<CreateFolderDialogComponent>,
    private apiService: ApiService,
    private toaster: ToastrService,
  ) {
    this.folderService = this.data.dataService;
  }

  ngOnInit() {
    this.files = this.data.treeData;
    this.dataSource.data = this.files;
    this.treeControl.dataNodes = this.dataSource.data;
    this.treeControl.expandAll();
  }
  setSelectedNode() {
    if (this.data.destination_folder && this.data.destination_folder != '') {
      this.findNodeByPath(this.files, this.data.destination_folder);
    }
  }

  findNodeByPath(nodes: FileStructureNodeResponse[], filterText: string) {
    const filteredNodes: FileStructureNodeResponse[] = [];

    nodes.forEach((node: any) => {
      const children = node.children
        ? this.findNodeByPath(node.children, filterText)
        : [];

      if (node.full_path === filterText) {
        const newNode = { ...node, children };
        this.isFileSelected(node);
      }
    });
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

  async createFolder() {
    if (this.new_folder_name != '') {
      var currentUser = JSON.parse(localStorage.getItem('currentUser')!);
      let folderInfo = {
        folder_name: this.new_folder_name,
        destination_folder: '',
        user_id: currentUser._id,
      };
      let selectedNode: any = this.getSelectedNode();
      if (selectedNode) {
        folderInfo.destination_folder = selectedNode.full_path;
      } else {
        if (this.data.destination_folder != '') {
          folderInfo.destination_folder = this.data.destination_folder;
        }
      }

      this.folderService
        .createFolder(folderInfo)
        .then((response: any) => {
          if (response) {
            this.toaster.success('Folder created successfully', '', {
              positionClass: 'custom-toast-position',
            });
            this.dialogRef.close({ success: true });
          }
        })
        .catch((error: any) => {
          console.error('Error fetching mounted drive data:', error);
          this.toaster.error(error, '', {
            positionClass: 'custom-toast-position',
          });
        });
    }
  }
  close() {
    this.dialogRef.close({ success: false });
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
  disableCreate() {
    return this.new_folder_name == '' ? true : false;
  }
  filterNode(
    nodes: FileStructureNodeResponse[],
    filterText: string,
  ): FileStructureNodeResponse[] {
    const filteredNodes: FileStructureNodeResponse[] = [];

    nodes.forEach((node: any) => {
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

  
  isCreatingFolderInThisDatasetEnabled(node: any) {
    return !(node.dataset_type == "IMAGE_DATASET" || node.dataset_type == "IMAGES_FOLDER")
  }
}
