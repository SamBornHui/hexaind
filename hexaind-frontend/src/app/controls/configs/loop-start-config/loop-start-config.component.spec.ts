import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoopStartConfigComponent } from './loop-start-config.component';

describe('LoopStartConfigComponent', () => {
  let component: LoopStartConfigComponent;
  let fixture: ComponentFixture<LoopStartConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [LoopStartConfigComponent]
    });
    fixture = TestBed.createComponent(LoopStartConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
