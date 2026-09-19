import { Component, Inject } from "@angular/core";
import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { DataPreviewService } from '../services/data-preview.service'
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: "app-download-rescale-vizualize-data",
  templateUrl: "./download-rescale-vizualize-data.component.html",
  styleUrls: ["./download-rescale-vizualize-data.component.less"],
})
export class DownloadRescaleVisualizeDataComponent {
  displayedColumns: any[] = [
    "trial_index"
  ];
  projectId:string="";
  siteId:string="";
  constructor(@Inject(MAT_DIALOG_DATA) public data: any,
   public dialogRef: MatDialogRef<DownloadRescaleVisualizeDataComponent>,
   private dataPreviewService: DataPreviewService,
   private errorHandlerService:ErrorHandlerService,
   private route: ActivatedRoute) {
    this.route.queryParams.subscribe((params) => {
      this.projectId = params['projectId'];
      this.siteId = params['siteId'];
    });

  }
  ngOnInit() {
    
  }

  downloadFile() {
    var selectedData = this.data.trialsData.filter((data:any)=>data.selected);
    var mapData = selectedData.map((item:any) => {
      const newItem: any = {
        trial_index:item.trial_index,
        folder_path:item.visual_dir,
      };
      return newItem;
    });

    if(mapData.length>0){
      this.dataPreviewService
      .downloadVisualization(mapData)
      .subscribe({
        next: (blob: Blob) =>
          this.handleBlob(blob),
        error: (error: any) => {
          console.error('Download failed:', error);
          this.errorHandlerService.handleError(error);
        },
      });
    }
  }

  private handleBlob(
    blob: Blob
  ) {
    const blobUrl = window.URL.createObjectURL(blob);
    const fileName = `visualization.zip`;
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
    this.dialogRef.close({"success":true});
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
