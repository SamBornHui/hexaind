import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddToDatasetComponent } from './add-to-dataset.component';

describe('AddToDatasetComponent', () => {
  let component: AddToDatasetComponent;
  let fixture: ComponentFixture<AddToDatasetComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AddToDatasetComponent]
    });
    fixture = TestBed.createComponent(AddToDatasetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
