import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportDatasetDialogComponent } from './import-dataset-dialog.component';

describe('ImportDatasetDialogComponent', () => {
  let component: ImportDatasetDialogComponent;
  let fixture: ComponentFixture<ImportDatasetDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImportDatasetDialogComponent]
    });
    fixture = TestBed.createComponent(ImportDatasetDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
