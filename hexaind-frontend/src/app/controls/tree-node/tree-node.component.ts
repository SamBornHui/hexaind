import { Component, Input, Output, EventEmitter } from '@angular/core';
import { Utils, DirectoryItem } from '../../utils';

@Component({
  selector: 'app-tree-node',
  templateUrl: './tree-node.component.html',
  styleUrls: ['./tree-node.component.less'],
})
export class TreeNodeComponent {
  @Input() node!: DirectoryItem; // Adjust the type according to your data structure
  @Output() nodeClick = new EventEmitter<{ path: string; name: string }>();
  @Output() nodeDoubleClick = new EventEmitter<DirectoryItem>();

  static selectedNode: TreeNodeComponent | null = null;

  isExpanded: boolean = false;
  isSelected = false;

  // Inside TreeNodeComponent
  onSingleClick() {
    if (this.node!.type === 'folder') {
      this.isExpanded = !this.isExpanded;
      if (this.isExpanded) {
        this.nodeClick.emit({ path: this.node!.path, name: this.node!.name }); // Emit the path
      }
    } else {
      this.select();
    }
  }

  select() {
    if (TreeNodeComponent.selectedNode) {
      TreeNodeComponent.selectedNode.isSelected = false;
    }

    TreeNodeComponent.selectedNode = this;
    this.isSelected = true;
    // Other selection logic here
  }

  formatSize(node: DirectoryItem) {
    let size: string = Utils.FormatFileSize(parseFloat(node.size));
    return size;
  }

  onChildNodeSingleClick(eventData: { path: string; name: string }) {
    // Re-emit the event data from the child node
    this.nodeClick.emit(eventData);
  }

  onDoubleClick() {
    this.onChildNodeDoubleClicked(this.node);
  }

  onChildNodeDoubleClicked(node: any) {
    if (node.type == 'file') {
      this.nodeDoubleClick.emit(node);
    }
  }

  isPngFile(filename: string): boolean {
    return filename.toLocaleLowerCase().endsWith('.png');
  }

  isJpgFile(filename: string): boolean {
    return (
      filename.toLocaleLowerCase().endsWith('.jpg') ||
      filename.endsWith('.jepg')
    );
  }

  isTiffFile(filename: string): boolean {
    return (
      filename.toLocaleLowerCase().endsWith('.tiff') ||
      filename.endsWith('.tif')
    );
  }

  isPdfFile(filename: string): boolean {
    return filename.toLocaleLowerCase().endsWith('.pdf');
  }

  isCsvFile(filename: string): boolean {
    return filename.toLocaleLowerCase().endsWith('.csv');
  }
}
