import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ComparisonInstanceComponent } from './comparison-instance.component';

describe('ComparisonInstanceComponent', () => {
  let component: ComparisonInstanceComponent;
  let fixture: ComponentFixture<ComparisonInstanceComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ComparisonInstanceComponent]
    });
    fixture = TestBed.createComponent(ComparisonInstanceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
