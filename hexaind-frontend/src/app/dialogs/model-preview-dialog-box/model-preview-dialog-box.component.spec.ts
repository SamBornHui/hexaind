import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModelPreviewDialogBoxComponent } from './model-preview-dialog-box.component';

describe('ModelPreviewDialogBoxComponent', () => {
  let component: ModelPreviewDialogBoxComponent;
  let fixture: ComponentFixture<ModelPreviewDialogBoxComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ModelPreviewDialogBoxComponent]
    });
    fixture = TestBed.createComponent(ModelPreviewDialogBoxComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
