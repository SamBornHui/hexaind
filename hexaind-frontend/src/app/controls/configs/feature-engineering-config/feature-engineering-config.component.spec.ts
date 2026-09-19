import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FeatureEngineeringConfigComponent } from './feature-engineering-config.component';

describe('FeatureEngineeringConfigComponent', () => {
  let component: FeatureEngineeringConfigComponent;
  let fixture: ComponentFixture<FeatureEngineeringConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FeatureEngineeringConfigComponent]
    });
    fixture = TestBed.createComponent(FeatureEngineeringConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
