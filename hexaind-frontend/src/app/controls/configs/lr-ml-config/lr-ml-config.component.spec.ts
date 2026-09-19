import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LRMlConfigComponent } from './lr-ml-config.component';

describe('LRMlConfigComponent', () => {
  let component: LRMlConfigComponent;
  let fixture: ComponentFixture<LRMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [LRMlConfigComponent],
    });
    fixture = TestBed.createComponent(LRMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
