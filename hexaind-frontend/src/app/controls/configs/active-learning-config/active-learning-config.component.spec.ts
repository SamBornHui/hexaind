import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ActiveLearningConfigComponent } from './active-learning-config.component';

describe('ActiveLearningConfigComponent', () => {
  let component: ActiveLearningConfigComponent;
  let fixture: ComponentFixture<ActiveLearningConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ActiveLearningConfigComponent]
    });
    fixture = TestBed.createComponent(ActiveLearningConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
