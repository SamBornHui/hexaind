import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BigQueryLoadSavedQueryComponent } from './big-query-load-saved-query.component';

describe('BigQueryLoadSavedQueryComponent', () => {
  let component: BigQueryLoadSavedQueryComponent;
  let fixture: ComponentFixture<BigQueryLoadSavedQueryComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [BigQueryLoadSavedQueryComponent]
    });
    fixture = TestBed.createComponent(BigQueryLoadSavedQueryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
