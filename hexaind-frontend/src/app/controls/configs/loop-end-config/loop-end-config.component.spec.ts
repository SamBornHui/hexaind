import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoopEndConfigComponent } from './loop-end-config.component';

describe('LoopEndConfigComponent', () => {
  let component: LoopEndConfigComponent;
  let fixture: ComponentFixture<LoopEndConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [LoopEndConfigComponent]
    });
    fixture = TestBed.createComponent(LoopEndConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
