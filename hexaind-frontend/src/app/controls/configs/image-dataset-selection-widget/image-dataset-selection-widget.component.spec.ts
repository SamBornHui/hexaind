// import { ComponentFixture, TestBed } from '@angular/core/testing';

// import { ImageDatasetSelectionWidgetComponent } from './image-dataset-selection-widget.component';

// describe('ImageDatasetSelectionWidgetComponent', () => {
//   let component: ImageDatasetSelectionWidgetComponent;
//   let fixture: ComponentFixture<ImageDatasetSelectionWidgetComponent>;

//   beforeEach(() => {
//     TestBed.configureTestingModule({
//       declarations: [ImageDatasetSelectionWidgetComponent]
//     });
//     fixture = TestBed.createComponent(ImageDatasetSelectionWidgetComponent);
//     component = fixture.componentInstance;
//     fixture.detectChanges();
//   });

//   it('should create', () => {
//     expect(component).toBeTruthy();
//   });
// });

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ImageDatasetSelectionWidgetComponent } from './image-dataset-selection-widget.component';
import { ToastrModule } from 'ngx-toastr';
import { MatDialogModule } from '@angular/material/dialog';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ApiService } from 'src/app/services/api.service';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import {
  ImageDatasetSelectionWidgetConfig,
  ImageTypes
} from 'src/app/models/workflow-models';

fdescribe('ImageDatasetSelectionWidgetComponent', () => {
  let component: ImageDatasetSelectionWidgetComponent;
  let fixture: ComponentFixture<ImageDatasetSelectionWidgetComponent>;
  let apiService: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    const apiServiceSpy = jasmine.createSpyObj('ApiService', ['getImageDatasets']);

    await TestBed.configureTestingModule({
      declarations: [ImageDatasetSelectionWidgetComponent],
      imports: [
        MatDialogModule,
        ToastrModule.forRoot(),
        HttpClientTestingModule
      ],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy },
        WorkflowCanvasService,
        SharedDataService,
      ],
    }).compileComponents();

    apiService = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ImageDatasetSelectionWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should filter datasets based on selectedImageType', () => {
    component.imagesDatasets = [
      { dataset_id: '1', dataset_name: 'Dataset 1', dataset_location: 'tmp/path', segmented: true },
      { dataset_id: '2', dataset_name: 'Dataset 2', dataset_location: 'tmp/path', segmented: false },
    ];

    component.selectedImageType = ImageTypes.Segmented;
    const filtered = component.getFilteredDatasets(); // Assumes a `getFilteredDatasets` method exists.
    expect(filtered.length).toBe(1);
    expect(filtered[0].dataset_id).toBe('1');

    component.selectedImageType = ImageTypes.Raw;
    const filteredRaw = component.getFilteredDatasets();
    expect(filteredRaw.length).toBe(1);
    expect(filteredRaw[0].dataset_id).toBe('2');
  });

  it('should handle API errors gracefully', () => {
    spyOn(component.toaster, 'error');
    apiService.getImageDatasets.and.throwError('API Error');

    component.getImagesDatasets();

    expect(component.toaster.error).toHaveBeenCalledWith(
      'An unexpected error occurred',
      'ERROR',
      { positionClass: 'custom-toast-position' }
    );
  });

  it('should save selected datasets', () => {
    component.selectedDatasets = [
      { dataset_id: '1', dataset_name: 'Dataset 1', segmented: true },
    ];
    component.configCache = new ImageDatasetSelectionWidgetConfig();

    component.onSave();

    expect(component.configCache.image_datasets).toEqual([
      { dataset_id: '1', dataset_name: 'Dataset 1'},
    ]);
  });

  it('should cancel changes correctly', () => {
    const originalConfig = new ImageDatasetSelectionWidgetConfig();
    component.config = { ...originalConfig };
    component.configCache = new ImageDatasetSelectionWidgetConfig();
    component.configCache.image_datasets = [{ dataset_id: '1', dataset_name: 'Dataset 1' }];
    
    // component.configCache = {
    //   image_datasets: [{ dataset_id: '1', dataset_name: 'Dataset 1' }],
    // };

    component.onCancel();

    expect(component.configCache).toEqual(originalConfig);
    expect(component.changeMade).toBe(false);
  });
});

