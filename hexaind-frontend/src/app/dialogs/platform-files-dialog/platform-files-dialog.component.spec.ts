import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PlatformFilesDialogComponent } from './platform-files-dialog.component';

describe('CreateNewWorkflowComponent', () => {
  let component: PlatformFilesDialogComponent;
  let fixture: ComponentFixture<PlatformFilesDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PlatformFilesDialogComponent]
    });
    fixture = TestBed.createComponent(PlatformFilesDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
