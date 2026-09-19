import {
  Component,
  ChangeDetectorRef,
  HostListener,
  ViewChild,
} from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { ElementRef, Renderer2 } from '@angular/core';
import { DataStructureService } from './services/data-structure.service';
import {
  forkJoin,
  Observable,
  ObservableInput,
  of,
  Subject,
  Subscription,
} from 'rxjs';
import { catchError, debounceTime, elementAt } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { ModuleImportDialogComponent } from 'src/app/dialogs/module-import-dialog/module-import-dialog.component';
import { ModuleService } from './services/module.service';
import { DataImportDialogComponent } from 'src/app/dialogs/data-import/data-import-dialog.component';
import { Utils } from 'src/app/utils';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { MatMenuTrigger } from '@angular/material/menu';
import { NotificationComponent } from 'src/app/controls/notification/notification.component';
import { MountedDriveDataPreviewComponent } from 'src/app/dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import { CreateFolderDialogComponent } from 'src/app/dialogs/create-folder-dialog/create-folder-dialog.component';
import { ImportDatasetDialogComponent } from 'src/app/dialogs/import-dataset-dialog/import-dataset-dialog.component';
import { MoveDatasetDialogComponent } from 'src/app/dialogs/move-dataset-dialog/move-dataset-dialog.component';
import { DuplicateDatasetDialogComponent } from 'src/app/dialogs/duplicate-dataset-dialog/duplicate-dataset-dialog.component';
import { RenameFolderDialogComponent } from 'src/app/dialogs/rename-folder-dialog/rename-folder-dialog.component';

import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { TreeTableModule } from 'primeng/treetable';
import { TreeNode } from 'primeng/api';
import { ToastrService } from 'ngx-toastr';
import { FileStructureNodeResponse } from 'src/app/models/api-models';
import { VisualizeTextdataComponent } from 'src/app/dialogs/data-preview/visualize/visualize-textdata/visualize-textdata.component';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { DatasetType } from 'src/app/models/data-models';
import { EditImageFolderComponent } from 'src/app/dialogs/data-import/edit-image-folder/edit-image-folder.component';

import { ActivatedRoute, Router } from '@angular/router';
import { CodeMirrorEditorComponent } from 'src/app/monaco-editor/codemirror-editor.component';
import { CodeMirrorEditorService } from 'src/app/monaco-editor/codemirror-editor.service';
import { HttpClient } from '@angular/common/http';


@Component({
  selector: 'app-data-structure',
  templateUrl: './data-structure.component.html',
  styleUrls: ['./data-structure.component.less'],
})
export class DataStructureComponent {
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  private searchTerms = new Subject<string>();
  searchText: string = '';
  selectedWorkflowRow: any = null;
  showUserContextMenu = false;
  pageTitle: string = 'Datasets';
  dataSource: any;
  searchResults: any[] = [];
  searchModuleResults: any[] = [];
  moduleSource: any;
  assetType: string = 'dataset';
  selectedOwner: string = '';
  selectedSort: string = 'Most recent';
  numberOfColumns: number = 1;
  screenWidth: number = 0;
  dialogRef: any;
  private boundResizeFunction: () => void;
  private destroy$ = new Subject<void>();
  public deleteConfirmation: boolean = false;
  showDeleteConfirmation: boolean = false;
  descending: boolean = true;
  assets: any = {};

  @ViewChild('deleteConfirmation')
  deleteConfirmationMenu!: MatMenuTrigger;
  moreOptions: boolean = false;

  dataStructure: any = [];
  filteredDataStructure: any = [];
  currentFolderView: any = [];
  currentParent: any = {};
  breadcrumbItems: any[] = [];
  isContextMenuOpen = false;
  contextMenuPosition = { x: 0, y: 0 };
  treeTableData!: TreeNode[];
  folderView: boolean = false;
  folderDisplayType: string = 'grid';
  isFileUpload: boolean = true;
  isFolderUpload: boolean = false;
  imageDatasetThumbnails: { [key: string]: string } = {};
  private projectSubscription: Subscription | undefined = undefined;
  dataLoader: boolean = false;
  isDataSetLoaded: boolean = false;
  // Other component code
  // @HostListener('document:click', ['$event'])
  // clickOutside(event: Event) {
  //   if (!this.deleteConfirmationMenu.menuOpen) {
  //     this.resetDeleteConfirmation();
  //   }
  // }
  nfolder = [
    'wf_images',
    'segment_dir',
    'uploaded',
    'batchprocessed',
    'processedimg',
    'modifiedimages',
    'thumbnails',
    'images_metadata',
    '.ipynb_checkpoints',
  ];

  resetDeleteConfirmation() {
    this.showDeleteConfirmation = false;
  }

  constructor(
    private cdRef: ChangeDetectorRef,
    public navService: NavService,
    private renderer: Renderer2,
    private el: ElementRef,
    private dataService: DataStructureService,
    private moduleService: ModuleService,
    public dialog: MatDialog,
    private apiService: ApiService,
    private errorHandlerService: ErrorHandlerService,
    private toaster: ToastrService,
    private cdr: ChangeDetectorRef,
    private configService: ConfigService,
    private router: Router,
    private codeMirrorEditorService: CodeMirrorEditorService,
  ) {
    const rolesfeaturesString = localStorage.getItem('rolesfeatures');
    if (rolesfeaturesString !== null) {
      this.assets = JSON.parse(rolesfeaturesString).assets.datasets;
    } else {
      this.assets = 'server_admin';
      console.error('No rolesfeatures found in localStorage.');
    }

    this.renderer.listen('document', 'click', (event) => {
      if (this.el.nativeElement.contains(event.target)) {
        this.showUserContextMenu = false;
      }
    });

    this.searchTerms.pipe(debounceTime(500)).subscribe((term) => {
      this.searchText = term;
      if (this.assetType === 'dataset') {
        this.getFoldersData();
      }
    });

    this.boundResizeFunction = this.onResize.bind(this);
    window.addEventListener('resize', this.boundResizeFunction);
  }

  ngOnInit() {
    this.dataLoader = true;
    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe(
        (projectId: any) => {
          if (projectId) {
            this.folderView = false;
            this.getFoldersData();
          }
        },
      );
  }

  changeFolderDisplayView(type: string) {
    this.folderDisplayType = type;
  }

  onSearchTextChange(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    const filtered = this.filterTreeNode(this.filteredDataStructure, filterValue);
    this.treeTableData = this.convertData(filtered);
  }


  filterFolderNode(
    nodes: FileStructureNodeResponse[],
  ): FileStructureNodeResponse[] {
    const filteredNodes: FileStructureNodeResponse[] = [];
    nodes.forEach((node: any) => {
      const children = node.children
        ? this.filterFolderNode(node.children)
        : [];

      if (node.type == 'folder') {
        const newNode = { ...node, children };
        filteredNodes.push(newNode);
      }
    });

    return filteredNodes;
  }

  filterTreeNode(nodes: FileStructureNodeResponse[], filterText: string,): FileStructureNodeResponse[] {
    const filteredNodes: FileStructureNodeResponse[] = [];
    nodes.forEach((node: any) => {
      const children = node.children ? this.filterTreeNode(node.children, filterText) : [];
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

  backToTreeView() {
    this.folderView = false;
  }

  async fetchThumbNailsForImagesInFolder(children: any) {
    const imageThumbnailRequests: Observable<any>[] = [];
    let storeImageResponseIndex: any = [];

    children.forEach((child: any) => {
      if (child.data.dataset_type != 'IMAGE') return;
      imageThumbnailRequests.push(
        this.apiService
          .getImageDatasetThumbnail(
            child.data.dataset_path,
            '/thumbnails' + child.data.parent,
            child.data.name,
          )
          .pipe(
            catchError((error) => {
              return of(null);
            }),
          ),
      );
      storeImageResponseIndex.push(child.data.full_path);
    });

    forkJoin(imageThumbnailRequests).subscribe((results: any[]) => {
      results.forEach((result, index) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          this.imageDatasetThumbnails[storeImageResponseIndex[index]] =
            reader.result as string;
        };
        reader.readAsDataURL(result);
      });
      this.cdr.detectChanges();
    });
  }


  async switchToBreadCrumbView(rowData: any) {
    if (rowData.node.data.type === 'folder') {
      if (!rowData.node.children || rowData.node.children.length === 0) {
        await this.toggleRow(rowData);
      }
      this.folderView = true;
      if (rowData.node.data.dataset_type === 'IMAGES_FOLDER' || rowData.node.data.dataset_type === 'IMAGE_DATASET') {
        this.fetchThumbNailsForImagesInFolder(rowData.node.children);
      }
      this.currentFolderView = rowData.node.children || [];
      this.currentParent = {
        name: rowData.node.data.name,
        path: rowData.node.data.full_path,
        datasetType: rowData.node.data.dataset_type
      };

      this.createBreadCrumbItems(rowData.node);
    }
  }

  createBreadCrumbItems(element: any) {
    const itemPath: string | undefined = element.data.item_path;
    const parentFolder: string = element.data.dataset_name || element.data.name;
    const breadcrumbItems = [];
    breadcrumbItems.push({ label: 'Datasets', url: '/datasets' });

    if (parentFolder) {
      breadcrumbItems.push({ label: parentFolder, url: `/datasets/${parentFolder}` });
    }
    if (!itemPath) {
      this.breadcrumbItems = breadcrumbItems;
      return;
    }

    const segments = itemPath.split('/').filter(segment => segment !== '');
    let currentPath = '';

    for (let i = 0; i < segments.length; i++) {
      currentPath += `/${segments[i]}`;
      breadcrumbItems.push({
        label: segments[i],
        url: `/datasets/${parentFolder}${currentPath}`,
      });
    }

    this.breadcrumbItems = breadcrumbItems;
  }

  viewFolderResult(bcItem: any) {
    const parts = bcItem.url.split('/');
    if (parts.length < 3) {
      return;
    }

    const relativeSegments = parts.slice(3);
    const relativePath = relativeSegments.length > 0
      ? '/' + relativeSegments.join('/')
      : '';

    const findNode = (nodes: any[]): any => {
      for (const node of nodes) {
        if (node.data) {
          if (relativePath === '') {
            if (
              (node.data.dataset_name && node.data.dataset_name.toLowerCase() === bcItem.label.toLowerCase()) ||
              (node.data.name && node.data.name.toLowerCase() === bcItem.label.toLowerCase())
            ) {
              return node;
            }
          } else {
            if (
              node.data.item_path &&
              node.data.item_path.toLowerCase() === relativePath.toLowerCase()
            ) {
              return node;
            }
          }
        }
        if (node.children && node.children.length > 0) {
          const found = findNode(node.children);
          if (found) {
            return found;
          }
        }
      }
      return null;
    };

    const targetNode = findNode(this.treeTableData);
    if (targetNode) {
      this.currentFolderView = targetNode.children || [];
      this.currentParent = {
        name: targetNode.data.name,
        path: targetNode.data.full_path,
        datasetType: targetNode.data.dataset_type
      };
      this.createBreadCrumbItems(targetNode);
    } else {
      console.warn("No matching node found for breadcrumb URL:", bcItem.url);
    }
  }

  expandFolder(element: any) {
    if (element?.data?.type == 'folder') {
      this.currentFolderView = element.children;
      this.currentParent = {
        name: element.data.name,
        path: element.data.full_path,
        datasetType: element.data.dataset_type,
      };
      this.createBreadCrumbItems(element);
      this.fetchThumbNailsForImagesInFolder(element.children);
    }
  }



  addMissingInfo() {
    this.filteredDataStructure = [...this.dataStructure];
    this.treeTableData = this.convertData(this.filteredDataStructure);
  }

  convertData(data: any): any {
    // Step 1: Extract all file names without extensions to compare with folder names
    const fileNamesWithoutExtension = data
      .filter((item: any) => !item.is_folder) // Get only files
      .map((item: any) => item.name.split('.')[0].toLowerCase()); // Extract file name without extension and convert to lowercase

    // Step 2: Remove any folder that has the same name as a file
    const filteredData = data.filter((item: any) => {
      // Check if the item is a folder and its name (lowercase) matches any file name (without extension)
      if (
        item.is_folder &&
        fileNamesWithoutExtension.includes(item.name.toLowerCase())
      ) {
        return false; // Exclude this folder
      }
      return true; // Keep this item
    });

    return filteredData.map((item: any) => {
      const convertedItem: any = {
        data: {
          name: item.name,
          size: item.size ? item.size : '',
          type: item.type,
          last_modified_at: item.last_modified_at ? item.last_modified_at : '',
          full_path: item.full_path,
          is_corrputed: item.is_corrputed ? item.is_corrputed : false,
          _id: item._id ? item._id : '',
          project_id: item.project_id,
          parent_id: item.parent_id,
          site_id: item.site_id,
          created_by: item.created_by ? item.created_by : '',
          created_at: item.created_at
            ? item.created_at
            : item.last_modified_by
              ? item.last_modified_at
              : '',
          dataset_type: item.dataset_type ? item.dataset_type : '',
          dataset_path: item.dataset_path,
          dataset_name: item.dataset_name,
          item_path: item.item_path,
          extension: item.extension,
          description: item.description,
          metaDataFiles: this.extractMetadataFileNameIfPresentInChildren(item),
          parent: item.parent,
        },
        children: [],
      };

      if (item.children && item.children.length > 0) {
        convertedItem.children = this.convertData(item.children);
      }

      return convertedItem;
    });
  }


  isImportIntoExistingDatasetEnabled() {
    return (
      this.currentParent.datasetType != 'IMAGES_FOLDER' &&
      this.currentParent.datasetType != 'IMAGE_DATASET'
    );
  }

  /**
   * This function will replace the timestamp (which is the foldername where the data is stored) in the fullpath
   * with the dataset name. It also remove the uploaded folder but will not alter the original url
   */
  removeTimeStampIfDatasetIsImageType(
    breadcrumbItems: any,
    segment: string,
    element: any,
  ) {
    const isFolderNameUnixTimeStamp: boolean = /^\d{13}$/.test(segment);
    if (segment === 'uploaded') {
      breadcrumbItems.pop();
    }
    if (isFolderNameUnixTimeStamp) {
      breadcrumbItems[breadcrumbItems.length - 1].label = element.dataset_name
        ? element.dataset_name
        : element.name;
    }
  }

  getFoldersData() {
    this.isDataSetLoaded = false;
    this.apiService
      .getFolderStructureList('')
      .then((response) => {
        this.dataLoader = false;
        if (response) {
          this.dataStructure = response;
          const rootProject = this.dataStructure.find((item: any) => {
            const lastSegment = item.full_path.split('/').pop();
            return (
              item.dataset_type === 'FOLDER' &&
              !item.parent_id &&
              lastSegment.startsWith('p_')
            );
          });
          const rootProjectItems = rootProject ? rootProject.children : [];
          const otherItems = this.dataStructure.filter(
            (item: any) =>
              item !== rootProject && item.parent_id !== rootProject?._id,
          );
          this.filteredDataStructure = [...rootProjectItems, ...otherItems];
          this.filteredDataStructure.sort(
            (
              a: { last_modified_at: string },
              b: { last_modified_at: string },
            ) =>
              new Date(b.last_modified_at).getTime() -
              new Date(a.last_modified_at).getTime(),
          );

          this.treeTableData = this.convertData(this.filteredDataStructure);
          if (this.folderView) {
            this.findExpandedElement();
          }
          this.isDataSetLoaded = true;
        } else {
          this.dataStructure = [];
          this.filteredDataStructure = [];
        }
      })
      .catch((error) => {
        console.error('Error fetching mounted drive data:', error);
      });
  }

  findExpandedElement() {
    this.findNodeByPath(this.filteredDataStructure, this.currentParent.path);
  }

  findNodeByPath(nodes: FileStructureNodeResponse[], filterText: string) {
    const filteredNodes: FileStructureNodeResponse[] = [];

    nodes.forEach((node: any) => {
      const children = node.children
        ? this.findNodeByPath(node.children, filterText)
        : [];

      if (node.full_path === filterText) {
        this.expandFolder(node);
      }
    });
  }
  ngAfterViewInit() {
    this.screenWidth = window.innerWidth;

    setTimeout(() => {
      this.calculateColumns();
    }, 250);
  }

  ngOnDestroy() {
    // Remove the event listener when the component is destroyed
    window.removeEventListener('resize', this.boundResizeFunction);
    this.destroy$.next();
    this.destroy$.complete();
    this.projectSubscription?.unsubscribe();
  }

  onResize(event?: Event) {
    this.calculateColumns();
    this.screenWidth = window.innerWidth;
    this.cdRef.detectChanges();
  }

  private calculateColumns() {
    const parentWidth = document.querySelector('[fxLayout]')!.clientWidth; // Ensure this selects your flex container
    this.numberOfColumns = Utils.CalculateColumns(parentWidth);
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  async ConvertToCsv(rowData: any) {
    const data = {
      conversion_type: 'TABULAR_PARQUET_TO_CSV',
      from_config: {
        dataset_id: rowData._id,
      },
      to_config: {
        name: 'CSV',
      },
      retain_older: 'True',
    };
    await this.apiService.AssestDataModification(
      rowData.site_id,
      rowData.project_id,
      data,
    );
    this.getFoldersData();
  }

  getExtensionAndCheck(rowData: any, fileType: string): boolean {
    if (!rowData || !rowData.full_path) {
      return fileType === 'csv'; // Default to CSV if full_path is missing
    }

    const parts = rowData.full_path.split('.');
    const extension = parts.length > 1 ? parts.pop()?.toLowerCase() : ''; // Check if there is an extension

    return extension ? extension === fileType : fileType === 'csv'; // If no extension, default to CSV
  }

  isCsvFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'csv');
  }
  isTextFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'txt');
  }
  isTexFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'tex');
  }
  isPNGFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'png');
  }
  isJsonFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'json');
  }

  isParquetFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'parquet');
  }

  isPythonFile(rowData: any) {
    return this.getExtensionAndCheck(rowData, 'py');
  }

  isImageFile(rowData: any) {
    const extension = rowData.full_path?.split('.').pop().toLowerCase();
    return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif'].includes(extension)
      ? true
      : false;
  }

  isExcelFile(rowData: any) {
    const extension = rowData.full_path?.split('.').pop().toLowerCase();
    return ['xlsx', 'xls'].includes(extension)
      ? true
      : false;
  }

  isPDFFile(rowData: any) {
    const extension = rowData.full_path?.split('.').pop().toLowerCase();
    return extension === 'pdf' ? true : false;
  }

  isZipFile(rowData: any): boolean {
    const extension = rowData.full_path?.split('.').pop().toLowerCase();
    return extension === 'zip' ? true : false;
  }

  openDataPreviewDialog(dataset: any) {
    if (dataset._id) {
      let dialogRef;
      if (this.isTextFile(dataset) || this.isTexFile(dataset)) {
        dialogRef = this.dialog.open(VisualizeTextdataComponent, {
          width: '75vw',
          maxWidth: '75vw',
          height: '75%',
          data: {
            datasetId: dataset._id,
          },
        });
      }
      else if (this.isPNGFile(dataset)) {
        const dialogRef = this.dialog.open(DataPreviewComponent, {
          width: '75vw',
          maxWidth: '75vw',
          height: '95%',
          data: {
            datasetId: dataset._id,
            isPNG: true,
            full_path: dataset.full_path,
          },
        });
        dialogRef.afterClosed().subscribe(() => { });
      }
      else if (this.isPythonFile(dataset)) {
        this.openFileContentDialog(dataset, 'python');
      }
      else if (this.isJsonFile(dataset)) {
        this.openFileContentDialog(dataset, 'application/json');
      }
      else {
        dialogRef = this.dialog.open(DataPreviewComponent, {
          width: '95vw',
          maxWidth: '95vw',
          height: '95%',
          data: {
            datasetId: dataset._id,
            fileName: dataset.name,
            fullPath: dataset.full_path
          },
        });
      }
      if (dialogRef) {
        dialogRef.afterClosed().subscribe((result) => { });
      }
    }
  }

  showMountedDriveDialog() {
    const dialogRef = this.dialog.open(MountedDriveDataPreviewComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'csv',
        name: '',
        description: '',
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
      }
    });
  }

  openDatasetRenameDialog(element: any) {
    const dialogRef = this.dialog.open(RenameFolderDialogComponent, {
      width: '660px',
      data: {
        element: element,
        dataService: this.dataService,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.getFoldersData();
      }
    });
  }

  openCreateFolderDialog() {
    let destination_folder = '';
    if (this.folderView) {
      destination_folder = this.currentParent.path;
    }
    const dialogRef = this.dialog.open(CreateFolderDialogComponent, {
      height: '90%',
      width: '660px',
      data: {
        dataService: this.dataService,
        treeData: this.filterFolderNode(this.dataStructure),
        destination_folder: destination_folder,
      },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.getFoldersData();
      }
    });
  }

  importDataDialog(file_type: string) {
    let destination_folder = '';
    if (this.folderView) {
      destination_folder = this.currentParent.path;
    }
    const dialogRef = this.dialog.open(ImportDatasetDialogComponent, {
      height: '90%',
      width: '60%',
      data: {
        file_type: file_type,
        destination_folder: destination_folder,
        isMultiFileUpload: file_type == 'images' || file_type == 'Image Folder',
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result?.success) {
        this.getFoldersData();
        if (this.folderView) {
          const segments = this.currentParent.path.split('/').filter((segment: string) => segment !== '');
          const lastSegment = segments[segments.length - 1];
          const FolderItem = this.breadcrumbItems.find(item => item.label === lastSegment);
          setTimeout(() => {
            if (FolderItem) {
              this.viewFolderResult(FolderItem);
              this.cdr.detectChanges();
            } else {
              console.error('Breadcrumb item does not found');
            }
          }, 3000);
        }
      }
    });
  }

  datasetTypeForWhichFeaturesNotEnable = ['IMAGE'];

  isDatasetFeaturesEnabled(element: any) {
    return !this.datasetTypeForWhichFeaturesNotEnable.includes(
      element.dataset_type,
    );
  }

  fileSizeConveter(size: any) {
    if (size != '' && size != '0') {
      const sizesDataset = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      const iDataset = Math.floor(Math.log(size) / Math.log(1024));
      const convertedSize = `${parseFloat(
        (size / Math.pow(1024, iDataset)).toFixed(1),
      )} ${sizesDataset[iDataset]}`;
      return convertedSize;
    } else {
      return size;
    }
  }
  openMoveDatasetDialog(element: any) {
    const dialogRef = this.dialog.open(MoveDatasetDialogComponent, {
      height: '90%',
      width: '660px',
      data: {
        element: element,
        dataService: this.dataService,
        treeData: this.filterFolderNode(this.dataStructure),
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.getFoldersData();
      }
    });
  }
  openDuplicateDatasetDialog(element: any) {
    const dialogRef = this.dialog.open(DuplicateDatasetDialogComponent, {
      height: '90%',
      width: '660px',
      data: {
        element: element,
        dataService: this.dataService,
        treeData: this.filterFolderNode(this.dataStructure),
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.getFoldersData();
      }
    });
  }
  downloadData(element: any) {
    var fileName = '';
    if (element.type == 'file') {
      var fileNameSplit = element.full_path.split('.');
      fileName = element.name + '.' + fileNameSplit[1];
    } else {
      fileName = element.name + '.zip';
    }

    this.dataService
      .downloadDataFile({ source: element!.full_path })
      .subscribe({
        next: (blob: Blob) => this.handleBlob(blob, fileName),
        error: (error: any) => {
          this.errorHandlerService.handleError(error);
        },
      });
  }
  private handleBlob(blob: Blob, fileName: string) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
  }
  async deleteAsset(element: any) {
    this.dataService
      .deleteAsset({
        source: element!.full_path,
        dataset_type: element.dataset_type,
      })
      .then((response: any) => {
        if (response) {
          this.toaster.success('Deleted successfully', '', {
            positionClass: 'custom-toast-position',
          });
          this.getFoldersData();
        }
      })
      .catch((error: any) => {
        console.error('Error moving dataset:', error);
      });
  }

  lastAccessedDate(date: string) {
    if (!date.endsWith('Z')) {
      date += 'Z';
      return Utils.formatDateTime(date);
    } else {
      return Utils.formatDateTime(date);
    }
  }

  isCurrentParentDataSetImage() {
    return (
      this.currentParent.datasetType === 'IMAGES_FOLDER' ||
      this.currentParent.datasetType === 'IMAGE_DATASET'
    );
  }

  editImageFolderData(element: any) {
    let dimensions = {};
    if (element.dataset_type === 'IMAGE_DATASET') {
      dimensions = {
        height: '465px',
        width: '670px',
      };
    } else {
      dimensions = {
        height: '365px',
        width: '670px',
      };
    }
    const dialogRef = this.dialog.open(EditImageFolderComponent, {
      data: element,
      ...dimensions,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.getFoldersData();
      }
    });
  }

  /**
   * Currently only imageFolder and imageDataset had folder metadata
   */
  extractMetadataFileNameIfPresentInChildren(element: any) {
    if (
      element.dataset_type != 'IMAGES_FOLDER' &&
      element.dataset_type != 'IMAGE_DATASET'
    )
      return [];
    let metaDataFilesArray: any = [];
    let arrayInWhichMetadataFilePresent =
      element.dataset_type === 'IMAGE_DATASET'
        ? element.metadata
        : element.children;
    arrayInWhichMetadataFilePresent?.forEach((child: any) => {
      if (child.extension === 'CSV') {
        metaDataFilesArray.push(child);
      }
    });
    return metaDataFilesArray;
  }

  async deleteImageDatasetEntity(element: any) {
    await this.apiService.deleteImageDatasetEntity(
      element.dataset_path,
      element.full_path,
    );
    this.getFoldersData();
  }

  imageFeature(element: any, feature: string) {
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    let queryParams = { datasetName: element.name };
    let imageFeatureLink = `sites/${this.configService.SelectedSiteId}/projects/${this.configService.SelectedProjectId}/image-analysis/${element._id}/${feature}`;
    this.router.navigate([imageFeatureLink], {
      queryParams,
    });
  }

  getFileContent(dataset: any) {
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;

    if (!siteId || !selectedProjectId) {
      return undefined;
    }
    const data = {
      file_path: dataset.full_path,
      file_name: dataset.name,
    };

    return this.codeMirrorEditorService.getFileContent(siteId, selectedProjectId, data);
  }

  openFileContentDialog(dataset: any, mode: string) {
    const fileContent = this.getFileContent(dataset);
    if (fileContent) {
      fileContent.subscribe({
        next: (response) => {
          if (response?.content) {
            this.dialog.open(CodeMirrorEditorComponent, {
              width: '90%',
              height: '90%',
              data: {
                content: response.content,
                mode: mode
              },
            });
          } else {
            this.toaster.error('Unable to retrieve file content. Please try again later.', '', {
              positionClass: 'custom-toast-position',
            });
          }
        },
        error: (error) => {
          console.error('Error fetching file content:', error);
          this.toaster.error('Unable to retrieve file content.', '', {
            positionClass: 'custom-toast-position',
          });
        },
        complete: () => { }
      });
    } else {
      this.toaster.error('Unable to retrieve file content.', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  async toggleRow(rowNode: any): Promise<void> {
    const data = rowNode.node.data;
    if (data.dataset_type === 'IMAGE_DATASET' && (!rowNode.node.children || rowNode.node.children.length === 0)) {
      rowNode.node.expanded = true;
      rowNode.expanded = true;
      const payload = {
        name: data.name,
        dataset_type: data.dataset_type,
        full_path: data.full_path
      };
      data.loading = true;
      try {
        const response = await this.dataService.getChildrenForImageFolder(payload);
        if (response?.children?.length > 0) {
          const childrenData = response.children;

          const filteredIndex = this.filteredDataStructure.findIndex((item: any) => item.full_path === data.full_path);
          if (filteredIndex !== -1) {
            this.filteredDataStructure[filteredIndex].children = childrenData;
          }

          rowNode.node.children = this.convertData(childrenData);
        } else {
          const dummyData = {
            name: 'No data found',
            size: '',
            type: '',
            last_modified_at: '',
            created_by: '',
            created_at: '',
            isNoData: true
          };
          const dummyRow = {
            data: dummyData,
            children: [],
            isNoData: true
          };
          rowNode.node.children = [dummyRow];
        }
        this.treeTableData = [...this.treeTableData];
        this.cdRef.detectChanges();
      } catch (error) {
        console.error('Error fetching children for image dataset folder:', error);
      }
      data.loading = false;
    } else {
      rowNode.node.expanded = !rowNode.node.expanded;
      rowNode.expanded = rowNode.node.expanded;
      this.treeTableData = [...this.treeTableData];
    }
  }

}
