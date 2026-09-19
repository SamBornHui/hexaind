import { Component, OnInit } from '@angular/core';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { DataSheetGenerateService } from '../data-sheet-generate.service';
import { ToastrService } from 'ngx-toastr';
import { ConfirmationDialogComponent } from './confirmation-dialog/confirmation-dialog.component';
import { MatDialog } from '@angular/material/dialog';
import { NotificationService } from '../notification.service';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-dsg-files',
  templateUrl: './dsg-files.component.html',
  styleUrls: ['./dsg-files.component.less'],
})
export class DsgFilesComponent implements OnInit {
  showMainHeader: boolean = false;
  toggleHeaderButton: string = 'expand_more';
  initialFolders: string[] = [];
  initialData: any;
  childrenData: { [key: string]: any[] } = {};
  expandedNodes: { [key: string]: boolean } = {};
  projectId!: string;
  showConfirmation: boolean = false;
  confirmMessage: string = '';
  currentPath: string = '';
  allDataSheets: any;

  constructor(
    private configService: ConfigService,
    private datasheetService: DataSheetGenerateService,
    private router: Router,
    public toaster: ToastrService,
    public dialog: MatDialog,
    private notificationService: NotificationService
  ) {
    const selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (selectedProjectId) {
      this.projectId = selectedProjectId;
    }
  }

  ngOnInit() {
    this.fetchData();
  }

  navigate(pageName: string) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
  }

  toggleMainHeader(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

  fetchData() {
    const obj = { base_path: 'base' };
    this.datasheetService.getDataSheetNumber(obj, this.projectId)
      .pipe(
        switchMap((dataSheetsResponse: any) => {
          this.allDataSheets = dataSheetsResponse.datasheets
            .sort((a: any, b: any) => parseInt(a.datasheet) - parseInt(b.datasheet))
            .map((datasheet: any) => ({
              ...datasheet,
              tensile_ages: datasheet.tensile_ages
                .map((age: number) => age.toString())
                .sort((a: string, b: string) => parseInt(a) - parseInt(b)),
            }));
          const requestData = { base_path: 'base' };
          return this.datasheetService.getDatasheetDetails(requestData, this.projectId);
        })
      )
      .subscribe({
        next: (folderResponse: any) => {
          const sortedDatasheets = this.sortDatasheets(folderResponse.datasheets);
          this.initialData = sortedDatasheets.map((item: any) => {
            const matchingSheet = this.allDataSheets.find(
              (sheet: any) => sheet.datasheet === item.datasheet
            );
            return {
              ...item,
              locked: matchingSheet ? matchingSheet.locked : false
            };
          });
          this.initialFolders = this.initialData.map((item: any) =>
            typeof item === 'object' && item !== null ? item.datasheet : item
          );
          this.initialFolders.forEach((folder) => {
            this.expandedNodes[folder] = false;
          });
        },
        error: (error) => {
          this.notificationService.showError(error);
        }
      });
  }

  loadChildren(path: string) {
    if (this.isFilePath(path)) {
      return;
    }
    const requestData = { base_path: path };
    this.datasheetService.getDatasheetDetails(requestData, this.projectId).subscribe(
      (data) => {
        const sortedDatasheets = this.sortDatasheets(data.datasheets);
        this.childrenData[path] = sortedDatasheets;
        this.expandedNodes[path] = true;
      },
      (error) => {
        this.notificationService.showError(error);
      }
    );
  }

  private sortDatasheets(items: any[]): any[] {
    if (!Array.isArray(items)) return items;
    return items.sort((a, b) => {
      const valueA = (typeof a === 'object' && a !== null) ? a.datasheet ?? '' : (a ?? '');
      const valueB = (typeof b === 'object' && b !== null) ? b.datasheet ?? '' : (b ?? '');
      return valueA.localeCompare(valueB, undefined, { numeric: true, sensitivity: 'base' });
    });
  }

  onToggle(path: string) {
    if (this.expandedNodes[path]) {
      this.expandedNodes[path] = false;
    } else {
      if (!this.childrenData[path]) {
        this.loadChildren(path);
      } else {
        this.expandedNodes[path] = true;
      }
    }
  }

  async onDelete(path: string): Promise<void> {
    const parts = path.split('/');
    const rootFolder = parts[0];
    const subFolder = parts.length > 1 ? parts[1] : null;
    const nominalAgeStr = parts.length > 2 ? parts[2] : null;
    const nominalAge = nominalAgeStr ? parseInt(nominalAgeStr.split(' ')[0], 10) : null;

    const folderData = this.initialData.find((data: any) => data.datasheet === rootFolder);
    if (!folderData) {
      return;
    }

    // Determine if a prompt is required
    if (!subFolder && folderData.processed) {
      // Case 1: Root folder is processed
      this.showConfirmationBox(path);
      return;
    } else if (subFolder && !nominalAgeStr && folderData.nominal_age?.length > 0) {
      // Case 2: Subfolder with nominal ages
      this.showConfirmationBox(path);
      return;
    } else if (nominalAge !== null && folderData.nominal_age?.includes(nominalAge)) {
      // Case 3: Leaf folder contains nominal age
      this.showConfirmationBox(path);
      return;
    }

    // No prompt needed, proceed with deletion directly
    await this.performDelete(path);
  }

  showConfirmationBox(path: string): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '450px',
      data: {
        heading: 'Delete Confirmation',
        message: 'This folder contains processed files. Do you want to delete it?',
        confirmButton: 'Confirm',
        cancelButton: 'No',
      }
    });
    dialogRef.afterClosed().subscribe(async (result) => {
      if (!result) {
        return;
      }
      this.performDelete(path);
    });
  }

  async performDelete(path: string): Promise<void> {
    try {
      const result = await this.datasheetService.deleteDatasheet(this.projectId, path);
      if (result.message) {
        this.removeFolderRecursively(path);
        this.toaster.success(`Folder deleted successfully.`, '', {
          positionClass: 'custom-toast-position',
        });
      } else {
        this.notificationService.showError('Unexpected server response while deleting.');
      }
    } catch (error: any) {
      this.notificationService.showError(error);
    }
  }

  /**
   * Recursively remove the folder and all its descendants from
   * initialFolders, childrenData, and expandedNodes.
   */

  private removeFolderRecursively(path: string) {
    const lastSlashIndex = path.lastIndexOf('/');
    if (lastSlashIndex > 0) {
      const parentPath = path.substring(0, lastSlashIndex);
      const folderName = path.substring(lastSlashIndex + 1);
      if (this.childrenData[parentPath]) {
        this.childrenData[parentPath] = this.childrenData[parentPath].filter(
          (childName) => childName !== folderName
        );
      }
    } else {
      this.initialFolders = this.initialFolders.filter((folder) => folder !== path);
    }
    delete this.expandedNodes[path];

    if (this.childrenData[path]) {
      this.childrenData[path].forEach((childName) => {
        const childPath = path + '/' + childName;
        this.removeFolderRecursively(childPath);
      });
      delete this.childrenData[path];
    }
  }


  async onDownload(path: string): Promise<void> {
    try {
      const blob = await this.datasheetService.downloadFolder(this.projectId, path);
      const url = window.URL.createObjectURL(blob);
      const fileName = `${path.replace(/\//g, '_')}.zip`;
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      if (error instanceof Error) {
        this.notificationService.showError(error.message || 'Unable to download folder. Please try again.');
      } else {
        this.notificationService.showError('An unknown error occurred. Please try again.');
      }
    }
  }

  onUpload(event: { parentPath: string; formData: FormData; newFolderName: string }) {
    const { parentPath, formData, newFolderName } = event;
    const siteId = this.configService.SelectedSiteId;

    this.datasheetService.ingestData(formData, siteId, this.projectId).subscribe({
      next: (result) => {
        this.loadChildren(parentPath);
        this.expandedNodes[parentPath] = true;
        const fullFolderPath = parentPath + '/' + newFolderName;
        this.expandedNodes[fullFolderPath] = false;
      },
      error: (error) => {
        this.notificationService.showError('Error uploading folder. Please try again.');
      },
      complete: () => {
        this.toaster.success(
          `Folder uploaded successfully.`,
          '',
          { positionClass: 'custom-toast-position' }
        );
      },
    });
  }

  isFilePath(path: string): boolean {
    const fileExtensionPattern = /\.[^\/]+$/;
    return fileExtensionPattern.test(path);
  }

  isDatasheetLocked(datasheet: string): boolean {
    return this.initialData?.find((item: any) => item.datasheet === datasheet)?.locked || false;
  }
}
