import { Component, Input, OnInit, Output, EventEmitter, ViewChild } from '@angular/core';
import { MatMenu, MatMenuTrigger } from '@angular/material/menu';

@Component({
  selector: 'app-file-tree-node',
  templateUrl: './file-tree-node.component.html',
  styleUrls: ['./file-tree-node.component.less'],
})
export class FileTreeNodeComponent implements OnInit {
  @Input() path: string = '';
  @Input() level: number = 0;
  @Input() children: any[] = [];
  @Input() isExpanded: boolean = false;
  @Input() expandedNodes: { [key: string]: boolean } = {};
  @Input() childrenData: { [key: string]: any[] } = {};
  @Input() isFilePath!: (path: string) => boolean;
  @Input() isLocked: boolean = false;

  @Output() toggle = new EventEmitter<string>();
  @Output() delete = new EventEmitter<string>();
  @Output() download = new EventEmitter<string>();
  @Output() upload = new EventEmitter<{ parentPath: string; formData: FormData, newFolderName: string; }>();

  public hasChildren: boolean = false;
  formData: FormData = new FormData();
  folderName: string = '';


  @ViewChild('actionsMenuTrigger') actionsMenuTrigger!: MatMenuTrigger;
  @ViewChild('actionsMenu') actionsMenu!: MatMenu;
  @ViewChild('deleteMenu') deleteMenu!: MatMenu;

  ngOnInit() {
    this.hasChildren =
      this.children && this.children.length > 0 && !this.isFilePath(this.path);
  }

  onToggle() {
    this.toggle.emit(this.path);
  }

  trackByFn(index: number, item: any) {
    return item;
  }

  stopPropagation(event: Event) {
    event.stopPropagation();
  }

  confirmDelete() {
    this.delete.emit(this.path);
  }

  downloadDataset(event: Event) {
    event.stopPropagation();
    this.download.emit(this.path);
  }

  openDeleteConfirmation(): void {
    this.actionsMenuTrigger.closeMenu();
    this.actionsMenuTrigger.menu = this.deleteMenu;
    this.actionsMenuTrigger.openMenu();
  }

  closeDeleteMenu(): void {
    this.actionsMenuTrigger.closeMenu();
    this.actionsMenuTrigger.menu = this.actionsMenu;
  }

  onDirectorySelected(event: any) {
    const directory = event.target.files;
    if (!directory || directory.length === 0) {
      return;
    }
    this.folderName = directory[0]?.webkitRelativePath.split('/')[0] ?? 'Uploaded_Folder';
    this.formData = new FormData();
    for (let i = 0; i < directory.length; i++) {
      this.formData.append('files', directory[i], directory[i].name);
      this.formData.append('filePaths', this.path + '/' + directory[i].webkitRelativePath);
    }
    this.upload.emit({ parentPath: this.path, formData: this.formData, newFolderName: this.folderName, });
  }
}
