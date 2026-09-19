import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditImageFolderComponent } from './edit-image-folder.component';

describe('EditImageFolderComponent', () => {
  let component: EditImageFolderComponent;
  let fixture: ComponentFixture<EditImageFolderComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EditImageFolderComponent]
    });
    fixture = TestBed.createComponent(EditImageFolderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
