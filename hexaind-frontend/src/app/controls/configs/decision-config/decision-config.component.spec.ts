import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DecisionConfigComponent } from './decision-config.component';

describe('LgbmConfigComponent', () => {
  let component: DecisionConfigComponent;
  let fixture: ComponentFixture<DecisionConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DecisionConfigComponent]
    });
    fixture = TestBed.createComponent(DecisionConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
