import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BigQueryConfigComponent } from './big-query-config.component';

describe('BigQueryConfigComponent', () => {
  let component: BigQueryConfigComponent;
  let fixture: ComponentFixture<BigQueryConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [BigQueryConfigComponent]
    });
    fixture = TestBed.createComponent(BigQueryConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
