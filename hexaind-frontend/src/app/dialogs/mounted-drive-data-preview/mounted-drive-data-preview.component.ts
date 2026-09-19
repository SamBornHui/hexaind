import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ApiService } from '../../services/api.service';
import { MatTreeNestedDataSource } from '@angular/material/tree';
import { NestedTreeControl } from '@angular/cdk/tree';
import { SelectionModel } from '@angular/cdk/collections';
import { FileNodeResponse } from 'src/app/models/api-models';

@Component({
  selector: 'app-mounted-drive-data-preview',
  templateUrl: './mounted-drive-data-preview.component.html',
  styleUrls: ['./mounted-drive-data-preview.component.less'],
})
export class MountedDriveDataPreviewComponent {
  treeControl = new NestedTreeControl<FileNodeResponse>(
    (node) => node.children,
  );
  dataSource = new MatTreeNestedDataSource<FileNodeResponse>();
  selection = new SelectionModel<FileNodeResponse>(false);
  files: any = [];
  path: any;
  hasChild = (_: number, node: FileNodeResponse) => node.type === 'folder';
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<MountedDriveDataPreviewComponent>,
    private apiService: ApiService,
  ) { }

  ngOnInit() {

    this.apiService
      .getMountedDriveDirectoryList(undefined, this.data.type)
      .then((response) => {
        if (response) {
          this.files = [response];
          this.dataSource.data = this.files;
          this.treeControl.dataNodes = this.dataSource.data;
        }
      })
      .catch((error) => {
        console.error('Error fetching mounted drive data:', error);
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

  isFileSelected(node: FileNodeResponse) {
    return this.selection.isSelected(node);
  }

  getSelectedNode(): FileNodeResponse | null {
    return this.selection.selected.length ? this.selection.selected[0] : null;
  }

  onImport() {
    if (this.data.type === 'save') {
      this.dialogRef.close({ success: true, path: this.path });
    } else if (this.data.type === 'csv') {
      const selectedNode = this.getSelectedNode();
      if (selectedNode) {
        this.apiService
          .importMountedDriveFile(
            selectedNode.full_path!,
            selectedNode.name!,
            this.data.description,
            'EXTERNAL',
            '',
          )
          .then((response) => {
            if (response) {
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
                path: this.path,
              });
            }
          })
          .catch((error) => {
            console.error('Error fetching mounted drive data:', error);
          });
      } else {
        console.log('No node selected');
      }
    } else if (this.data.type === 'zip') {
      const selectedNode = this.getSelectedNode();
      if (selectedNode) {
        this.dialogRef.close({
          success: true,
          name: selectedNode.name,
          pathname: selectedNode.full_path,
        });
      } else {
        console.log('No node selected');
      }
    } else {
      const selectedNode = this.getSelectedNode();
      if (selectedNode) {
        this.apiService
          .importMountedDriveFile(
            selectedNode.full_path!,
            this.data.name,
            this.data.description,
            'INTERNAL',
            '',
          )
          .then((response) => {
            if (response) {
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
                path: this.path,
              });
            }
          })
          .catch((error) => {
            console.error('Error fetching mounted drive data:', error);
          });
      } else {
        console.log('No node selected');
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

  filterNode(
    nodes: FileNodeResponse[],
    filterText: string,
  ): FileNodeResponse[] {
    const filteredNodes: FileNodeResponse[] = [];

    nodes.forEach((node) => {
      const children = node.children
        ? this.filterNode(node.children, filterText)
        : [];

      if (
        node.name!.toLowerCase().includes(filterText.toLowerCase()) ||
        children.length > 0
      ) {
        const newNode = { ...node, children };
        filteredNodes.push(newNode);
      }
    });

    return filteredNodes;
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
    this.apiService.getMountedDriveDirectoryList(node.full_path, this.data.type)
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
