import { ComponentFixture, TestBed } from '@angular/core/testing';

import { XgboostMlConfigComponent } from './xgboost-ml-config.component';

describe('XgboostMlConfigComponent', () => {
  let component: XgboostMlConfigComponent;
  let fixture: ComponentFixture<XgboostMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [XgboostMlConfigComponent]
    });
    fixture = TestBed.createComponent(XgboostMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
