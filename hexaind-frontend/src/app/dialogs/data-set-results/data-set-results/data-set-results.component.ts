import { SelectionModel } from '@angular/cdk/collections';
import { NestedTreeControl } from '@angular/cdk/tree';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatTreeNestedDataSource } from '@angular/material/tree';
import { FileNodeResponse } from 'src/app/models/api-models';
import { Workflow } from 'src/app/models/workflow-models';
import { ActionResultType, DatasetWidgetResult, WidgetRunResult, WorkflowSession } from 'src/app/models/workflow-sessions-api-response.models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/services/config.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { DataPreviewComponent } from '../../data-preview/data-preview.component';
import { DataPreviewService } from '../../data-preview/services/data-preview.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ImageVideoPreviewComponent } from 'src/app/dialogs/image-video-preview/image-video-preview.component';``


@Component({
  selector: 'app-data-set-results',
  templateUrl: './data-set-results.component.html',
  styleUrls: ['./data-set-results.component.less']
})
export class DataSetResultsComponent {
  dataSource = new MatTreeNestedDataSource<FileNodeResponse>();
  selection = new SelectionModel<FileNodeResponse>(false);
  selectionPreview = new SelectionModel<FileNodeResponse>(false);
  files: any = [];
  path: any;
  treeControl = new NestedTreeControl<FileNodeResponse>((node) => node.children,);
  hasChild = (_: number, node: FileNodeResponse) => !!node.children && node.children.length > 0;
  fileTreeData: FileNodeResponse[] = [];
  loading: boolean = false;
  datasets: { [key: string]: string } = {};
  nodeType: any;
  
  constructor(
    public dialogRef: MatDialogRef<DataSetResultsComponent>,
    private apiService: ApiService,
    private configService: ConfigService,
    private workflowCanvasService: WorkflowCanvasService,
    private sessionApi: WorkflowsSessionsApiService,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private dialog: MatDialog,
    private dataPreviewService: DataPreviewService,
    private errorHandlerService:ErrorHandlerService,
  ) { }

  ngOnInit() {
    if (this.data.runId) {
      this.loadDatasetResultsForVersionedWorkflowRun();
    } else {
      this.loadDatasetResultsForWorkflowSessionRun();
    }    
  }

  toggleFileSelection(node: any) {
    this.selection.toggle(node);
    if (node.type === 'file') {
      this.path = node.full_path;
      this.nodeType = node.type;
    } else if (node.type === 'directory') {
      this.selection.clear();
      this.path = node.full_path;
      this.nodeType = node.type;
    } else if(node.type == 'image/video'){      
      this.selectionPreview.toggle(node);
      this.nodeType = node.type;
      this.path = node.full_path;
    } else if(node.type == 'folder'){      
      this.selectionPreview.clear();
      this.nodeType = node.type;
      this.path = node.full_path;
    }
  }

  isFileSelected(node: FileNodeResponse) { 
    return this.selection.isSelected(node);
  }

  extractFileName(path: string): string {
    // Split the path by '/' and return the last element of the array
    return path.split('/').pop()!;
  }

  extractFolderPath(path: string): string {
    const parts = path.split('/');
    parts.pop(); // Remove the last segment, which is the file name
    return parts.join('/');
  }

  getValueByKey(key: string): string | undefined {
    return this.datasets[key];
  }

  addKeyValuePair(key: string, value: string): void {
    this.datasets[key] = value;
  }

  async loadDatasetResultsForVersionedWorkflowRun() {
    this.loading = true;

    // Fetch workflow information
    const workflow = await this.apiService.GetWorkflowById(
      this.configService.SelectedSiteId,
      this.configService.SelectedProjectId!,
      this.data.workflowId!
    );

    if (!workflow) {
      console.error('Workflow not found.');
      this.loading = false;
      return;
    }

    // Base file tree structure
    const rootFileNode = new FileNodeResponse();
    rootFileNode.children = [];
    rootFileNode.full_path = '/';
    rootFileNode.type = 'directory';
    rootFileNode.name = workflow.name;
    this.fileTreeData.push(rootFileNode);

    // Sets for checking unique file names and paths
    const uniqueFileNames = new Set<string>();
    const uniquePaths = new Set<string>();
    const uniqueTrailNumbers = new Set<string>();

    for (const widget of workflow.widgets) {
      const widgetUrn = widget.urn;
      const results = await this.sessionApi.GetVersionedWorkflowWidgetRunStatus(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId!,
        this.data.workflowId,
        this.data.runId,
        widgetUrn!
      );

      if (!results) {
        continue; // No results for this widget, move on
      }

      for (const result of results) {
        if (result.result_type === 'DATASET') {
          const datasetWidgetResult = result.result_value as DatasetWidgetResult;

          if (datasetWidgetResult?.dataset_location) {
            for (const location of datasetWidgetResult.dataset_location) {
              const path = location?.path;

              if (path) {
                const fileName = this.extractFileName(path);

                if (!uniquePaths.has(path) && !uniqueFileNames.has(fileName)) {
                  uniquePaths.add(path);
                  uniqueFileNames.add(fileName);

                  if (!datasetWidgetResult._id) {
                    console.error(`Error: _id is undefined for file '${fileName}'`);
                    continue;
                  }

                  // Add key-value mapping and new file node
                  this.addKeyValuePair(fileName, datasetWidgetResult._id);

                  const newFileNode = new FileNodeResponse();
                  newFileNode.full_path = path;
                  newFileNode.type = 'file';
                  newFileNode.name = fileName;

                  rootFileNode.children.push(newFileNode);
                } else {
                  console.warn(`Duplicate path or file name detected: ${fileName}. Skipping.`);
                }
              }
            }
          }

          // Handle custom information and trail data
          // Initialize the set outside the loop or block to keep track of unique trail numbers
          

          if (datasetWidgetResult?.custom_information?.custom_information?.trail_data) {
            const trailData = datasetWidgetResult.custom_information.custom_information.trail_data;

            trailData.forEach((trail: { trail_number: string; media_files: any[]; }) => {
              // Check if the trail number has already been processed
              if (!uniqueTrailNumbers.has(trail.trail_number)) {
                uniqueTrailNumbers.add(trail.trail_number); // Add to set to avoid duplicates

                const trailNode = new FileNodeResponse();
                trailNode.name = `Trial ${trail.trail_number}`;
                trailNode.children = [];
                trailNode.type = 'folder';

                // Add media files to the trail node
                if (Array.isArray(trail.media_files)) {
                  trail.media_files.forEach((file) => {
                    const mediaNode = new FileNodeResponse();
                    mediaNode.full_path = file.path;
                    mediaNode.name = this.extractFileName(file.path);
                    mediaNode.type = 'image/video';

                    trailNode.trail = parseInt(trail.trail_number, 10);
                    trailNode.full_path = this.extractFolderPath(file.path);
                    trailNode.children.push(mediaNode);
                  });
                }

                // Add the new trail node to the root file tree
                rootFileNode.children.push(trailNode);
              } else {
                console.warn(`Duplicate trail number detected: ${trail.trail_number}. Skipping.`);
              }
            });
          }

        }
      }
    }

    // Update data source and tree control
    this.dataSource.data = this.fileTreeData;
    this.treeControl.dataNodes = this.dataSource.data;
    this.treeControl.expandAll();

    this.loading = false;
  }
  

  async loadDatasetResultsForWorkflowSessionRun() {
    this.loading = true;

    let workflow: Workflow | undefined = await this.apiService.GetWorkflowById(
      this.configService.SelectedSiteId,
      this.configService.SelectedProjectId!,
      this.data.workflowId!);
    if (workflow) {
      // let fileNodeResponse: FileNodeResponse = new FileNodeResponse();
      // fileNodeResponse.children = [];
      // fileNodeResponse.full_path = '/';
      // fileNodeResponse.type = 'directory';
      // fileNodeResponse.name = workflow.name;
      const rootFileNode = new FileNodeResponse();
      rootFileNode.children = [];
      rootFileNode.full_path = '/';
      rootFileNode.type = 'directory';
      rootFileNode.name = workflow.name;
      this.fileTreeData.push(rootFileNode);
      // this.fileTreeData.push(fileNodeResponse);
      const uniqueFileNames = new Set<string>();
      const uniquePaths = new Set<string>();
      const uniqueTrailNumbers = new Set<string>();
      for (let i = 0; i < workflow.widgets.length; i++) {
        let widgetUrn = workflow.widgets[i].urn;
        let results: WidgetRunResult[] = await this.sessionApi.GetWorkflowSessionWidgetRunStatus(
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId!,
          this.data.workflowSessionId,
          widgetUrn!);
        if (results) {
          results.forEach(result => {
            if (result) {
              if (result.result_type === ActionResultType.DATASET) {
                let datasetWidgetResult: DatasetWidgetResult = result.result_value as DatasetWidgetResult;

                if (datasetWidgetResult 
                  && datasetWidgetResult.custom_information 
                  && datasetWidgetResult.custom_information.custom_information 
                  && datasetWidgetResult.custom_information.custom_information.trail_data) {
                    
                const trailData = datasetWidgetResult.custom_information.custom_information.trail_data;
              
                if (Array.isArray(trailData)) {
                    trailData.forEach((trail: { trail_number: string; media_files: any[]; }) => {
                      if (!uniqueTrailNumbers.has(trail.trail_number)) {
                        uniqueTrailNumbers.add(trail.trail_number);
  
                        // Create the trail node
                        const trailNode = new FileNodeResponse();
                        trailNode.name = `Trial ${trail.trail_number}`;
                        trailNode.children = [];
  
                        // Add media files to trail node
                        if (trail.media_files && Array.isArray(trail.media_files)) {
                          trail.media_files.forEach((file) => {
                            const mediaNode = new FileNodeResponse();
                            mediaNode.full_path = file.path;
                            mediaNode.name = this.extractFileName(file.path);
                            mediaNode.type = 'file';
                            trailNode.trail = parseInt(trail.trail_number);
                            trailNode.children.push(mediaNode);
                          });
                        }
  
                        // Add the trail node to the main file tree
                        this.fileTreeData[0].children.push(trailNode);
                      }
                    });
                  } 
                }


                if (datasetWidgetResult?.dataset_location) {
                  for (const location of datasetWidgetResult.dataset_location) {
                    const path = location?.path;
      
                    if (path) {
                      const fileName = this.extractFileName(path);
      
                      if (!uniquePaths.has(path) && !uniqueFileNames.has(fileName)) {
                        uniquePaths.add(path);
                        uniqueFileNames.add(fileName);
      
                        if (!datasetWidgetResult._id) {
                          continue;
                        }
                        let widgetFileName = datasetWidgetResult?.name
                        let widgetName = '';
                        if(workflow?.widgets)
                        widgetName = workflow.widgets[i]?.name;
                        const existingNode = this.findNodeByWidgetName(this.fileTreeData,widgetName)
                        
                        // Add key-value mapping and new file node
                        this.addKeyValuePair(fileName, datasetWidgetResult._id);
                        

                        //create instance for file
                        const newFileNode = new FileNodeResponse();
                        newFileNode.full_path = path;
                        newFileNode.type = 'file';
                        newFileNode.name = widgetFileName;
                        newFileNode.widget = widgetName

                        if(!existingNode){
                          //create instance for folder
                          const newFolderNode = new FileNodeResponse();
                          newFolderNode.full_path = path;
                          newFolderNode.type = 'directory';
                          if(workflow?.widgets)
                          newFolderNode.name = widgetName
                          newFolderNode.children = [];
                          newFolderNode.widget = widgetName
                          newFolderNode.children.push(newFileNode)
                          rootFileNode.children.push(newFolderNode);
                        }
                        else{                          
                          existingNode.children.push(newFileNode)
                        }                        
                      }
                    }
                  }
                }
              }
            }
          });
        }
      }
      this.dataSource.data = this.fileTreeData;
      this.treeControl.dataNodes = this.dataSource.data;
      this.treeControl.expandAll();
    }
    this.loading = false;
  }

  findNodeByWidgetName(nodes: FileNodeResponse[], widgetName: string): FileNodeResponse | undefined {
    for (let node of nodes) {
    if (node.widget === widgetName) {
      return node;
    }
    const result = this.findNodeByWidgetName(node.children, widgetName);
    if (result) {
      return result;
    }
    }
      return undefined;
  }

  getSelectedNode(): FileNodeResponse | null { 
    return this.selection.selected.length ? this.selection.selected[0] : null;
  }
  
  onPreviewSelectedResult() {
    let selectedNode = this.getSelectedNode();
    if (!selectedNode) {
      return;
    }    
    let isPNG;
    let full_path;
    if(selectedNode?.full_path)
    full_path = this.extractFileName(selectedNode?.full_path);
    let fileName = selectedNode.name;
    let datasetId = this.getValueByKey(full_path!);
    const fileExtension = selectedNode.full_path?.split('.').pop()?.toLowerCase();
    if (fileExtension === 'png' || fileExtension === 'mp4') {        
        const dialogRef = this.dialog.open(ImageVideoPreviewComponent, {
          width: '50vw',
          maxWidth: '95vw',
          height: '95%',
          data: {
            fileExtension: fileExtension,
            selectedNode: selectedNode
          },
        });
        dialogRef.afterClosed().subscribe(() => { });
    } else {
      isPNG = false;
      if (datasetId) {
        const dialogRef = this.dialog.open(DataPreviewComponent, {
          width: '95vw',
          maxWidth: '95vw',
          height: '95%',
          data: {
            datasetId: datasetId,
            fileName: fileName,
            fullPath: full_path
          },
        });
        dialogRef.afterClosed().subscribe(() => { });
      }
    }
  }

  onDownloadSelectedResult() {
    let selectedNode = this.getSelectedNode();
    if (!selectedNode) {
      return;
    }else{
      if(selectedNode!.full_path !=""){
       let fileName = `${selectedNode!.name}`
        this.apiService
        .downloadWorkflowResultData([{file_path:selectedNode!.full_path}])
        .subscribe({
          next: (blob: Blob) =>
            this.handleBlob(blob,fileName),
          error: (error: any) => {
            console.error('Download failed:', error);
            this.errorHandlerService.handleError(error);
          },
        });
      }      
      if(selectedNode.type == 'folder'){
        const jsonData = [{
          trial_index: selectedNode.trail,
          folder_path:selectedNode!.full_path,
        }]
        this.dataPreviewService
        .downloadVisualization(jsonData)
        .subscribe({
          next: (blob: Blob) =>
            this.handleFolderBlob(blob), 
          error: (error: any) => {
            console.error('Download failed:', error);
            this.errorHandlerService.handleError(error);
          },
        });
      }
    }
  }

  filterNodes(event: Event) {
    const filterText = (event.target as HTMLInputElement)?.value;
    if (!filterText) {
      this.dataSource.data = this.fileTreeData;
      this.treeControl.expandAll();
    } else {
      this.dataSource.data = this.filterNode(this.fileTreeData, filterText);
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

  
  private handleFolderBlob(
    blob: Blob
  ) {
    const blobUrl = window.URL.createObjectURL(blob);
    const fileName = `visualization_folder.zip`;
    this.triggerFolderDownload(blobUrl, fileName);
  }

  private triggerFolderDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
    this.dialogRef.close({"success":true});
  }

  private handleBlob(
    blob: Blob,
    fileName:string
  ) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    
    let nameWithoutExtension: string;
    if (fileName.includes('.')) {
        nameWithoutExtension = fileName.split('.').slice(0, -1).join('.');
    } else {
        nameWithoutExtension = fileName;
    }

    link.setAttribute('download', nameWithoutExtension+'.zip');
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
  }

  enableDownloadButton(){
    var selectedData = this.data.trialsData.filter((data:any)=>data.selected);
    if(selectedData.length>0){
      return false;
    }else{
      return true;
    }

  }

}
