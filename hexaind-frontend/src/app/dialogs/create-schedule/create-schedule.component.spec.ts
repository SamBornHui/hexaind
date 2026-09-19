import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateNewScheduleComponent } from './create-schedule.component';

describe('CreateNewProjectComponent', () => {
  let component: CreateNewScheduleComponent;
  let fixture: ComponentFixture<CreateNewScheduleComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CreateNewScheduleComponent]
    });
    fixture = TestBed.createComponent(CreateNewScheduleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
