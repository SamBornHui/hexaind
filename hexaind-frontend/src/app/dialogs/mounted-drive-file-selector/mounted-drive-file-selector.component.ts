import { Component, Output, EventEmitter, Input } from '@angular/core';
import { Utils, DirectoryItem } from '../../utils';
import { ApiService } from 'src/app/services/api.service';
import { WidgetControl } from 'src/app/controls/widget-control/widget-control';
import {
  DataCopyWidgetConfig,
  MountedDriveConfiguration,
} from 'src/app/models/workflow-models';

@Component({
  selector: 'app-mounted-drive-file-selector',
  templateUrl: './mounted-drive-file-selector.component.html',
  styleUrls: ['./mounted-drive-file-selector.component.less'],
})
export class MountedDriveFileSelectorComponent {
  @Input() widgetControl: WidgetControl | undefined = undefined;
  @Output() closePanelClicked = new EventEmitter<any>();

  mountedDrive: string | null = null;
  directoryContent: DirectoryItem[] | null = null;
  selectedRemoteFile: string | null = null;
  fileSize: string | null = null;

  constructor(private apiService: ApiService) {}

  onClosePanel() {
    this.closePanelClicked.emit();
  }

  async onFileNodeDoubleClick(node: DirectoryItem) {
    this.selectedRemoteFile = node.path + '\\' + node.name;
    // this.ingestActivity.csvHeadersWithTypes =
    //   await this.apiService.GetCsvColumns(this.selectedRemoteFile);
    // this.ingestActivity!.columnCount =
    //   this.ingestActivity.csvHeadersWithTypes.length;
    let dataCopyActivityConfig = this.widgetControl!.Widget
      .config as DataCopyWidgetConfig;
    let mountedDriveConfiguration = dataCopyActivityConfig.source!
      .configuration as MountedDriveConfiguration;
    // mountedDriveConfiguration.original_file_name = this.selectedRemoteFile;

    // let extension = mountedDriveConfiguration.original_file_name
    //   .split('.')
    //   .pop()
    //   ?.toLowerCase();
    // mountedDriveConfiguration.file_type = Utils.GetFileType(extension!);
    // mountedDriveConfiguration.dataset_size = node.size;

    this.onClosePanel();
  }

  async loadNodeContent(path: string, folder: string | null) {
    if (folder !== null) {
      path = path + '\\' + folder;
    }
    let data = await this.apiService.ListDirectoryOnServer(path);
    if (data) {
      for (let node of data) {
        node.path = path;
      }
      this.updateNodeChildren(path, data);
    }
  }

  updateNodeChildren(path: string, children: DirectoryItem[]) {
    const findAndUpdateNode = (
      nodes: DirectoryItem[],
      targetPath: string,
    ): boolean => {
      for (const node of nodes) {
        if (
          node.type === 'folder' &&
          node.path + '\\' + node.name === targetPath
        ) {
          node.children = children;
          return true; // Node found and updated
        }
        if (node.type === 'folder' && node.children) {
          const found = findAndUpdateNode(node.children, targetPath);
          if (found) return true; // Node found in subtree
        }
      }
      return false; // Node not found in this branch
    };

    if (!this.directoryContent) {
      this.directoryContent = children;
    } else {
      findAndUpdateNode(this.directoryContent, path);
    }
  }
}
