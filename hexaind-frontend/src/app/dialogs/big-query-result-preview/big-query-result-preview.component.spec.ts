import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BigQueryResultPreviewComponent } from './big-query-result-preview.component';

describe('BigQueryResultPreviewComponent', () => {
  let component: BigQueryResultPreviewComponent;
  let fixture: ComponentFixture<BigQueryResultPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [BigQueryResultPreviewComponent]
    });
    fixture = TestBed.createComponent(BigQueryResultPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
