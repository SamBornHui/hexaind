import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MoveDatasetDialogComponent } from './move-dataset-dialog.component';

describe('MoveDatasetDialogComponent', () => {
  let component: MoveDatasetDialogComponent;
  let fixture: ComponentFixture<MoveDatasetDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MoveDatasetDialogComponent]
    });
    fixture = TestBed.createComponent(MoveDatasetDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
