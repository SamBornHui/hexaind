import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BigQueryPreviewComponent } from './big-query-preview.component';

describe('MyModelComponent', () => {
  let component: BigQueryPreviewComponent;
  let fixture: ComponentFixture<BigQueryPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [BigQueryPreviewComponent]
    });
    fixture = TestBed.createComponent(BigQueryPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
