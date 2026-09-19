import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShowDatasetDialogComponent } from './show-dataset-dialog.component';

describe('ShowDatasetDialogComponent', () => {
  let component: ShowDatasetDialogComponent;
  let fixture: ComponentFixture<ShowDatasetDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ShowDatasetDialogComponent]
    });
    fixture = TestBed.createComponent(ShowDatasetDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
