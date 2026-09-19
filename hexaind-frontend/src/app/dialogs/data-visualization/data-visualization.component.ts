import { Component, Inject, QueryList, Renderer2, ViewChild, ViewChildren } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ConfigService, WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from 'src/app/controls/widget-control/widget-control';
import { catchError, forkJoin, of } from 'rxjs';
import { ModelsService } from 'src/app/pages/models/services/models.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { MatExpansionPanel } from '@angular/material/expansion';

@Component({
  selector: 'app-data-visualization',
  templateUrl: './data-visualization.component.html',
  styleUrls: ['./data-visualization.component.less'],
})
export class DataVisualizationComponent {
  plots: any[] = [];
  isLoading: boolean[] = [];
  files: any[] = [];
  loader: boolean = false;
  isExpanded = false;
  @ViewChildren(MatExpansionPanel) panels: QueryList<MatExpansionPanel> | undefined;
  groupedFiles: { folder_name: string, images: any[] }[] = [];
  public widgetControl: WidgetControl | undefined = undefined;
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<DataVisualizationComponent>,
    private configService: ConfigService,
    private modelsService: ModelsService,
    public errorHandlerService: ErrorHandlerService,
    private renderer: Renderer2
  ) {
  }

  ngOnInit() {
    if (this.data.string_value === false) {
      this.loader = true;
      const pngFiles = this.data.plots.filter((plot: string) => plot.endsWith('.png'));
      this.preloadImages(pngFiles)
    } else {
      this.isLoading = Array(this.data.plots.length).fill(true);
    }
  }

  onPlotLoad(index: number): void {
    this.isLoading[index] = false;
  }

  preloadImages(files: any[]): void {
    this.files = [];
    const filteredFiles = files.filter(path => !path.includes("mod_"));

    forkJoin(
      filteredFiles.map((file) =>
        this.modelsService.CPWFileContent(file).pipe(
          catchError((error) => {
            return of(null);
          }),
        ),
      ),
    ).subscribe({
      next: (results) => {
        results.forEach((result, index) => {
          if (result) {
            const parts = filteredFiles[index].split('/');
            const folder_name = parts[parts.length - 3];
            const file_name = this.getFileNameWithoutExtension(filteredFiles[index]);
            this.files.push({
              name: file_name,
              folder_name: folder_name,
              imageUrl: result,
            });
            this.groupedFiles = this.groupByFolder(this.files);
          } else {
            console.error('Result is null ${index}');
            this.loader = false;
          }
        });
      },
      error: (error) => {
        console.error('Error loading images:', error);
        this.errorHandlerService.handleError(error);
        this.loader = false;
      },
      complete: () => {
        this.loader = false;
      },
    });
  }
  
  groupByFolder(files: any[]): { folder_name: string, images: any[] }[] {
    const grouped = files.reduce((acc, file) => {
      const folder = acc.find((group: { folder_name: any; }) => group.folder_name === file.folder_name);
      if (folder) {
        folder.images.push(file);
      } else {
        acc.push({ folder_name: file.folder_name, images: [file] });
      }
      return acc;
    }, []);
    return grouped;
  }

  getFileNameWithoutExtension(filePath: string): string {
    const fileNameWithExtension = filePath.substring(filePath.lastIndexOf('/') + 1);
    return fileNameWithExtension.substring(0, fileNameWithExtension.lastIndexOf('.')) || fileNameWithExtension;
  }


  toggleAllPanels() {
    if (this.panels) {
      this.panels.forEach(panel => {
        panel.expanded = !this.isExpanded;
      });
      this.isExpanded = !this.isExpanded;
    } else {
      console.error('Panels reference is undefined');
    }
  }
}
