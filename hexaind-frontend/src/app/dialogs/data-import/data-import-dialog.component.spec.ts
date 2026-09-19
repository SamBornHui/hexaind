import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataImportDialogComponent } from './data-import-dialog.component';

describe('DataImportDialogComponent', () => {
  let component: DataImportDialogComponent;
  let fixture: ComponentFixture<DataImportDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DataImportDialogComponent]
    });
    fixture = TestBed.createComponent(DataImportDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
