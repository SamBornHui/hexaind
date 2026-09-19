import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MountedDriveFileSelectorComponent } from './mounted-drive-file-selector.component';

describe('MountedDriveFileSelectorComponent', () => {
  let component: MountedDriveFileSelectorComponent;
  let fixture: ComponentFixture<MountedDriveFileSelectorComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MountedDriveFileSelectorComponent]
    });
    fixture = TestBed.createComponent(MountedDriveFileSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
