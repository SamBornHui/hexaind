import { Component, ChangeDetectorRef, TemplateRef, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ConfigService } from 'src/app/services/config.service';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { ToastrService } from 'ngx-toastr';
import { Location } from '@angular/common';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
(window as any).global = window;

interface FeaturesConfig {
  name: string;
  value: string;
}

@Component({
  selector: 'app-images',
  templateUrl: './images.component.html',
  styleUrls: ['./images.component.less'],
})
export class ImagesComponent {
  feature: string = 'details'
  projectId: string = ''
  siteId: string = '1'
  datasetId: string = ''
  datasetName: string = ''

  featuresList: FeaturesConfig[] = [
    // {name:'Details',value:'details'},
    {name:'Cleanup',value:'cleanup'},
    {name:'Segment',value:'segment'},
    {name:'Annotate',value:'annotate'}
  ]
  featureName = 'segmentation';
  @ViewChild('confirmationDialogTemplate') confirmationDialogTemplate!: TemplateRef<any>;
  dialogRef!: MatDialogRef<any>;
  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
    private imageAnalysisService: ImageAnalysisService,
    private toaster : ToastrService,
    private location: Location,
    private configService:ConfigService,
    private dialog: MatDialog,
  ) {
  }

  ngOnInit(): void {
    if (this.activatedRoute) {

      this.activatedRoute.params.subscribe(params => {
        this.siteId = params['siteId'];
        this.projectId = params['projectId'];
        this.datasetId = params['datasetId'];
        this.feature = params['feature'];
      });
  
      this.activatedRoute.queryParams.subscribe((params) => {
        this.datasetName = params['datasetName']
      });
    }
  }
  

  ngAfterViewInit() {
  }

  ngOnDestroy() {
  }

  onResize(event?: Event) {
  }
  switchFeatureView(feature:string){
    // this.feature = feature;
    let queryParams = { datasetName: this.datasetName };
    let imageFeatureLink = `sites/${this.configService.SelectedSiteId}/projects/${this.configService.SelectedProjectId}/image-analysis/${this.datasetId}/${feature}`;
    this.router.navigate([imageFeatureLink], {
      queryParams,
    });
  }
  goBack(){
    // this.location.back();
    var linkToNavigate = `sites/${this.configService.SelectedSiteId}/projects/${this.configService.SelectedProjectId}/data-structure`
    this.router.navigate([linkToNavigate]);
    this.dialogRef.close();
  }

  openConfirmationDialog(): void {
    this.dialogRef = this.dialog.open(this.confirmationDialogTemplate);
  }
  
}
