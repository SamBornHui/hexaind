import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { AutoMlConfigComponent } from './auto-ml-config.component';
import { MatDialogModule } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { MoboConfigService } from '../mobo-config/mobo-config.service';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ToastrService } from 'ngx-toastr';
import { SettingsComponent } from '../settings/settings.component';
import { AutoMLWidgetConfig, InputOutputConfig, RequestType, Widget, WidgetState, WidgetType } from 'src/app/models/workflow-models';
import { WidgetClientTags } from 'src/app/pages/workflow-designer/client-tags';
import { WidgetControl } from '../../widget-control/widget-control';

describe('AutoMlConfigComponent', () => {
  let component: AutoMlConfigComponent;
  let fixture: ComponentFixture<AutoMlConfigComponent>;

  beforeEach(async () => {
    const mockInputOutputConfig: InputOutputConfig = {
      name: 'input1',
      urn: 'urn:input1',
      map_to_argument: 'arg1',
      type: RequestType.DATASET
    };

    const mockWidget: Widget = {
      _id: '1',
      urn: 'urn:widget1',
      name: 'Mock Widget',
      description: 'A mock widget for testing',
      type: WidgetType.AUTOML,
      config: {} as AutoMLWidgetConfig,
      state: WidgetState.IDLE,
      on_success: [],
      on_failure: [],
      on_complete: [],
      inputs: [mockInputOutputConfig],
      outputs: [mockInputOutputConfig],
      use_gpu: false,
      retry_interval_in_sec: 30,
      retry_count: 3,
      client_tags: {} as WidgetClientTags,
      widget_id: 'widget_1'
    };

    const mockWidgetControl: WidgetControl = {
      Widget: mockWidget,
      ConnectorPoints: [],
      ZIndex: 1,
      GetPositionX: () => 0,
      GetPositionY: () => 0,
      GetWidth: () => 0,
      GetHeight: () => 0,
      GetColor: () => '',
      isSelected: false, // Add this missing property
      backgroundColor: '#ffffff',
    };


    const workflowCanvasServiceStub = {
      selectedWidgetControl: mockWidgetControl,
      findConnectedWidgets: () => [],
      findConnectedMLWidget: () => [],
    };

    const moboConfigServiceStub = {
      getDataset: () => of({ statistics: [{ column_names: [], row_names: [], data: [] }] }),
    };

    const sharedDataServiceStub = {};
    const toasterServiceStub = { error: jasmine.createSpy('error') };

    await TestBed.configureTestingModule({
      declarations: [AutoMlConfigComponent, SettingsComponent],
      imports: [MatDialogModule],
      providers: [
        { provide: WorkflowCanvasService, useValue: workflowCanvasServiceStub },
        { provide: MoboConfigService, useValue: moboConfigServiceStub },
        { provide: SharedDataService, useValue: sharedDataServiceStub },
        { provide: ToastrService, useValue: toasterServiceStub },
        { provide: ActivatedRoute, useValue: { queryParams: of({ projectId: '123' }) } },
      ],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AutoMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create AutoMlConfigComponent', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize component properties', () => {
    expect(component.configCache).toBeDefined();
    expect(component.settingsComponent).toBeDefined();
  });
});
