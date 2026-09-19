import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataPreviewDataComponent } from './data.component';

describe('DataPreviewDataComponent', () => {
  let component: DataPreviewDataComponent;
  let fixture: ComponentFixture<DataPreviewDataComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DataPreviewDataComponent]
    });
    fixture = TestBed.createComponent(DataPreviewDataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
