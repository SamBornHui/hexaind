import { Component, Inject } from '@angular/core';
import {
  MatDialog,
  MatDialogRef,
  MAT_DIALOG_DATA,
} from '@angular/material/dialog';
import { ApiService } from '../../services/api.service';
import { MatTreeNestedDataSource } from '@angular/material/tree';
import { NestedTreeControl } from '@angular/cdk/tree';
import { SelectionModel } from '@angular/cdk/collections';
import { FileNodeResponse } from 'src/app/models/api-models';
import { DataImportDialogComponent } from 'src/app/dialogs/data-import/data-import-dialog.component';
import { ModuleImportDialogComponent } from 'src/app/dialogs/module-import-dialog/module-import-dialog.component';
import { ToastrService } from 'ngx-toastr';
import { FeatureFlagService } from 'src/app/services/feature-flag.service';
import { AccessMode } from 'src/app/models/data-models';


@Component({
  selector: 'app-import-dataset-dialog',
  templateUrl: './import-dataset-dialog.component.html',
  styleUrls: ['./import-dataset-dialog.component.less'],
})
export class ImportDatasetDialogComponent {
  selectedOption: string = 'local';
  treeControl = new NestedTreeControl<FileNodeResponse>(
    (node) => node.children,
  );
  dataSource = new MatTreeNestedDataSource<FileNodeResponse>();
  selection = new SelectionModel<FileNodeResponse>(false);
  files: any = [];
  path: any;
  permittedExtensions: string = '';
  isMultiFileUpload: boolean = false;
  arrayOfFilesPathTobeUploaded: string[] = []
  mountedLoader: boolean = false;
  hasChild = (_: number, node: FileNodeResponse) => node.type === 'folder';
  isLoading: boolean = false;
  accessMode: string = AccessMode.EXTERNAL;
  tags: string[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ImportDatasetDialogComponent>,
    private apiService: ApiService,
    public dialog: MatDialog,
    private toaster: ToastrService,
    private featureFlagService: FeatureFlagService
  ) { }

  ngOnInit() {
    this.filePermitted(this.data.file_type);
    this.isMultiFileUpload = this.data.isMultiFileUpload
    if (this.isMultiFileUpload && this.data.file_type == 'images') this.selection = new SelectionModel<FileNodeResponse>(true);

    if (this.data.accessMode && this.data.accessMode != '') {
      this.accessMode = this.data.accessMode;
    }
    if (this.data.tags && this.data.tags.length > 0) {
      this.tags = this.data.tags;
    }
  }
  fetchMountedData() {
    if (this.files.length == 0) {
      this.getFoldersList();
    }
  }
  getFoldersList() {
    if (this.data.file_type != '') {
      this.mountedLoader = true;
      this.apiService.getMountedDriveDirectoryList('', this.data.file_type)
        .then((response) => {
          this.mountedLoader = false;
          if (response) {
            this.files = [response];
            this.dataSource.data = this.files;
            this.treeControl.dataNodes = this.dataSource.data;

          }
        })
        .catch((error) => {
          this.mountedLoader = false;
          console.error('Error fetching mounted drive data:', error);
        });
    }
  }

  filePermitted(fileType: string) {
    if (fileType.toLowerCase() === 'python') {
      this.permittedExtensions = '.py';
    } else if (fileType.toLowerCase() === 'csv') {
      this.permittedExtensions = '.csv';
    } else if (fileType.toLowerCase() === 'parquet') {
      this.permittedExtensions = '.parquet';
    } else if (fileType.toLowerCase() === 'json') {
      this.permittedExtensions = '.json';
    } else if (fileType.toLowerCase() === 'text') {
      this.permittedExtensions = '.txt';
    } else if (fileType.toLowerCase() === 'module') {
      this.permittedExtensions = '.zip';
    } else if (fileType === 'Image Folder' || fileType.toLowerCase() === 'folder') {
      this.permittedExtensions = 'folder';
    } else if (fileType.toLowerCase() === 'images') {
      this.permittedExtensions = '.jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp'
    } else if (fileType.toLowerCase() === 'excel') {
      this.permittedExtensions = '.xlsx,.xls'
    }
    else {
      this.permittedExtensions = '';
    }
  }
  toggleFileSelection(node: any) {
    this.selection.toggle(node);
    if (node.type === 'file') {
      this.path = node.full_path;
    } else if (node.type === 'folder') {
      this.path = node.full_path;
    }
  }

  isFileSelected(node: FileNodeResponse) {
    return this.selection.isSelected(node);
  }

  getSelectedNode(): FileNodeResponse | null {
    return this.selection.selected.length ? this.selection.selected[0] : null;
  }

  onImport() {
    const selectedNode: any = this.getSelectedNode();
    if (this.data.file_type == 'images' || this.data.file_type == 'Image Folder') {
      this.uploadImagesViaMountedDrive();
      return;
    }
    if (selectedNode) {
      var fileNameSplit = selectedNode.full_path.split('.');
      let data: any = {
        source: this.selectedOption,
        file: {
          full_path: selectedNode.full_path,
          name: selectedNode.name,
          description: this.data.description,
          access_mode: this.accessMode,
        },
        file_type: this.data.file_type.toLocaleUpperCase(),
        destination_folder: this.data.destination_folder,
      };

      if (this.tags.length > 0) {
        data['tags'] = this.tags
      }

      if (fileNameSplit[1] == 'py') {
        const dialogRef = this.dialog.open(ModuleImportDialogComponent, {
          width: '560px',
          data: data,
        });
        dialogRef.afterClosed().subscribe((result) => {
          if (result.success) {
            this.toaster.success('Dataset created successfully', '', {
              positionClass: 'custom-toast-position',
            });
            this.dialogRef.close({ success: true, module_id: result['module_id'] });
          }
        });
      } else {
        const dialogRef = this.dialog.open(DataImportDialogComponent, {
          width: '560px',
          data: data,
        });
        dialogRef.afterClosed().subscribe((result) => {
          if (result.success) {
            this.toaster.success('Dataset created successfully', '', {
              positionClass: 'custom-toast-position',
            });
            this.dialogRef.close({ success: true });
          }
        });
      }
    }
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

  filterNode(nodes: FileNodeResponse[], filterText: string): FileNodeResponse[] {
    const filteredNodes: FileNodeResponse[] = [];
    nodes.forEach((node: any) => {
      const children = node.children ? this.filterNode(node.children, filterText) : [];
      if (node.name.toLowerCase().includes(filterText.toLowerCase()) || children.length > 0) {
        const newNode = { ...node, children: children.length > 0 ? children : node.children };
        filteredNodes.push(newNode);
      }
    });
    return filteredNodes;
  }

  uploadFile($event: any) {
    if (this.permittedExtensions == '.py') {
      this.uploadModule($event);
    } else if (this.permittedExtensions == '.zip') {
      this.uploadModule($event);
    } else if (this.data.file_type === 'images') {
      this.uploadImageData($event, false)
    } else {

      let data: any = {
        source: this.selectedOption,
        file: $event.target.files[0],
        file_type: this.data.file_type.toLocaleUpperCase(),
        destination_folder: this.data.destination_folder,
        accessMode: this.accessMode

      }
      if (this.tags.length > 0) {
        data['tags'] = this.tags
      }

      const dialogRef = this.dialog.open(DataImportDialogComponent, {
        width: '560px',
        data: data
      });
      dialogRef.afterClosed().subscribe((result) => {
        if (result.success) {
          this.dialogRef.close({ success: true });
        }
      });
    }
  }

  async uploadImageData($event: any, isFolderUpload: boolean) {

    const files = $event.target.files;
    const formData = new FormData();
    let destinationFolder = ""
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (isFolderUpload) formData.append('files', file, file.webkitRelativePath);
      else formData.append('files', file)
    }

    if (this.data.destination_folder.length) {
      destinationFolder = this.data.destination_folder
    }

    try {
      // Show loader
      this.isLoading = true;

      // Wait for the API response
      const uploadApiResponse: any = await this.apiService.uploadImages(formData, 'uploaded', destinationFolder);

      // Do something with the response
      if (uploadApiResponse.base_folder != "" && destinationFolder != "") {
        this.dialogRef.close({ success: true });
        return
      }

      const dialogRef = this.dialog.open(DataImportDialogComponent, {
        width: '560px',
        data: {
          source: this.selectedOption,
          file_type: this.data.file_type,
          destination_folder: this.data.destination_folder,
          metadata: uploadApiResponse,
          uploadType: 'image',
          isMultiFileUpload: true
        },
      });
      dialogRef.afterClosed().subscribe((result) => {
        if (result?.success) {
          this.dialogRef.close({ success: true });
        }
        else {
          this.dialogRef.close({ success: false })
        }
      });

    } catch (error) {
      // Handle error if needed
      console.error("Error uploading images:", error);
      this.isLoading = false;
      this.toaster.error('Error uploading images', '', { positionClass: 'custom-toast-position' });

    } finally {
      // Hide loader after the response is received
      this.isLoading = false;
    }
  }

  async uploadImagesViaMountedDrive() {

    let destinationFolder = ""
    let filePathArray = this.selection.selected.map(mountedDriveElement => {
      return mountedDriveElement.full_path
    })
    if (this.data.destination_folder.length) {
      destinationFolder = this.data.destination_folder
    }

    let uploadApiResponse: any = await this.apiService.uploadImageDataToMountedDrive('uploaded', filePathArray, destinationFolder)
    if (uploadApiResponse.base_folder != "" && destinationFolder != "") {
      this.dialogRef.close({ success: true });
      return
    }

    const dialogRef = this.dialog.open(DataImportDialogComponent, {
      width: '560px',
      data: {
        source: this.selectedOption,
        file_type: this.data.file_type,
        destination_folder: this.data.destination_folder,
        metadata: uploadApiResponse,
        uploadType: 'image',
        isMultiFileUpload: true
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.dialogRef.close({ success: true });
      }
    });

  }

  uploadModule($event: any) {
    const dialogRef = this.dialog.open(ModuleImportDialogComponent, {
      width: '560px',
      data: {
        source: this.selectedOption,
        file: $event.target.files[0],
        file_type: this.data.file_type.toLocaleUpperCase(),
        destination_folder: this.data.destination_folder,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.dialogRef.close({ success: true, module_id: result['module_id'] });
      }
    });
  }

  showFileTypeInDialog() {

    let finalStringTobeShown = ""
    const { file_type } = this.data;

    switch (file_type) {
      case "images":
        finalStringTobeShown = "image";
        break
      case "Image Folder":
        finalStringTobeShown = file_type
        break
      case null:
      case undefined:
        finalStringTobeShown = ""
        break
      default:
        finalStringTobeShown = this.data.file_type.toLocaleUpperCase()
        break
    }

    return finalStringTobeShown
  }

  isLocalFileUplaodFeatureDisabled() {
    return this.featureFlagService.featureFlags['disableLocalFileUpload']
  }

  onNodeToggle(node: FileNodeResponse, event: Event) {
    event.stopPropagation();
    if (this.treeControl.isExpanded(node)) {
      if (!node.loaded) {
        this.fetchChildrenForNode(node)
      }
      else {
        this.treeControl.expand(node);
      }
    } else {
      this.treeControl.collapse(node);
    }
  }

  fetchChildrenForNode(node: FileNodeResponse) {
    const expandedNodes = this.treeControl.expansionModel.selected;
    this.apiService.getMountedDriveDirectoryList(node.full_path, this.data.file_type)
      .then((response: any) => {
        const transformedChildren = (response || []).map((child: any) => ({
          ...child,
          children: [],
          loaded: false
        }));
        const newData = this.updateNodeInData(
          this.dataSource.data,
          node.full_path,
          oldNode => ({
            ...oldNode,
            children: transformedChildren,
            loaded: true
          })
        );
        this.files = newData;
        this.dataSource.data = newData;
        this.treeControl.dataNodes = this.dataSource.data;

        expandedNodes.forEach(prevNode => {
          const updated = this.findNodeInData(this.dataSource.data, prevNode.full_path);
          if (updated) {
            this.treeControl.expand(updated);
          }
        });
        const updatedNode = this.findNodeInData(this.dataSource.data, node.full_path);
        if (updatedNode) {
          this.treeControl.expand(updatedNode);
        }
      })
      .catch((error: any) => {
        console.error('Error loading children:', error);
      });
  }

  private updateNodeInData(
    nodes: FileNodeResponse[],
    targetPath: any,
    updateFn: (node: FileNodeResponse) => FileNodeResponse
  ): FileNodeResponse[] {
    return nodes.map(node => {
      if (node.full_path === targetPath) {
        return updateFn(node);
      }

      return {
        ...node,
        children: node.children
          ? this.updateNodeInData(node.children, targetPath, updateFn)
          : node.children
      };
    });
  }

  private findNodeInData(nodes: FileNodeResponse[], targetPath: any): FileNodeResponse | null {
    for (const node of nodes) {
      if (node.full_path === targetPath) return node;
      if (node.children) {
        const found = this.findNodeInData(node.children, targetPath);
        if (found) return found;
      }
    }
    return null;
  }

}
