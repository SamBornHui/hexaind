import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModelsSummaryComponent } from './models-summary.component';

describe('ModelsSummaryComponent', () => {
  let component: ModelsSummaryComponent;
  let fixture: ComponentFixture<ModelsSummaryComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ModelsSummaryComponent]
    });
    fixture = TestBed.createComponent(ModelsSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
