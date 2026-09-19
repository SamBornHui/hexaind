import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FeaturesListCommonComponent } from './features-list-common.component';

describe('FeaturesListCommonComponent', () => {
  let component: FeaturesListCommonComponent;
  let fixture: ComponentFixture<FeaturesListCommonComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FeaturesListCommonComponent]
    });
    fixture = TestBed.createComponent(FeaturesListCommonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
