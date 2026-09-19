import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MountedDriveDataPreviewComponent } from './mounted-drive-data-preview.component';

describe('MountedDriveDataPreviewComponent', () => {
  let component: MountedDriveDataPreviewComponent;
  let fixture: ComponentFixture<MountedDriveDataPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MountedDriveDataPreviewComponent]
    });
    fixture = TestBed.createComponent(MountedDriveDataPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
