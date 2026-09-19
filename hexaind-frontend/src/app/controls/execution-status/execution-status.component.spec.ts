import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExecutionStatusComponent } from './execution-status.component';

describe('ExecutionStatusComponent', () => {
  let component: ExecutionStatusComponent;
  let fixture: ComponentFixture<ExecutionStatusComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ExecutionStatusComponent]
    });
    fixture = TestBed.createComponent(ExecutionStatusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
