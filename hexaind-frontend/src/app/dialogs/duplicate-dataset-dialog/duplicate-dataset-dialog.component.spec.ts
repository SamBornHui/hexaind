import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DuplicateDatasetDialogComponent } from './duplicate-dataset-dialog.component';

describe('DuplicateDatasetDialogComponent', () => {
  let component: DuplicateDatasetDialogComponent;
  let fixture: ComponentFixture<DuplicateDatasetDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DuplicateDatasetDialogComponent]
    });
    fixture = TestBed.createComponent(DuplicateDatasetDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
