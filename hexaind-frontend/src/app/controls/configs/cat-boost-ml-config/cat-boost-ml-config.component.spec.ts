import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CatBoostMlConfigComponent } from './cat-boost-ml-config.component';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';

describe('CatBoostMlConfigComponent', () => {
  let component: CatBoostMlConfigComponent;
  let fixture: ComponentFixture<CatBoostMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CatBoostMlConfigComponent]
    });
    fixture = TestBed.createComponent(CatBoostMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

describe('Dialog Opening', () => {
  let dialog: MatDialog;
  let dialogRef: MatDialogRef<ModelPreviewDialogBoxComponent>;

  let fixture: ComponentFixture<CatBoostMlConfigComponent>; // Declare the 'fixture' variable

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CatBoostMlConfigComponent]
    });
    fixture = TestBed.createComponent(CatBoostMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    dialog = TestBed.inject(MatDialog);
    dialogRef = dialog.open(ModelPreviewDialogBoxComponent, {
      width: '95vw',
      maxWidth: '95vw',
      height: '95%',
    });
  });

  let component: CatBoostMlConfigComponent; // Declare the 'component' variable
  class ModelPreviewDialogBoxComponent {
    dialogConfig!: {
      width: string;
      maxWidth: string;
      height: string;
    };
    // ... rest of the component code
  }

  it('should open the dialog with correct height', () => {
    const mockData = { view: 'someView' }; // Mock data to pass as the argument
    component.openModelPreveiwDialog(mockData); // Pass the mock data
    expect(dialogRef.componentInstance.dialogConfig.height).toEqual('95%');
  });

});