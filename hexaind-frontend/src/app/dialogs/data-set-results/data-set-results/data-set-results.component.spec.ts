import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataSetResultsComponent } from './data-set-results.component';

describe('DataSetResultsComponent', () => {
  let component: DataSetResultsComponent;
  let fixture: ComponentFixture<DataSetResultsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DataSetResultsComponent]
    });
    fixture = TestBed.createComponent(DataSetResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
