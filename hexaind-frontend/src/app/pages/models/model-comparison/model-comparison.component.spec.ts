import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModelComparisonComponent } from './model-comparison.component';

describe('ModelComparisonComponent', () => {
  let component: ModelComparisonComponent;
  let fixture: ComponentFixture<ModelComparisonComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ModelComparisonComponent]
    });
    fixture = TestBed.createComponent(ModelComparisonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
