import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NotificationDailogComponent } from './notification-dailog.component';

describe('NotificationDailogComponent', () => {
  let component: NotificationDailogComponent;
  let fixture: ComponentFixture<NotificationDailogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [NotificationDailogComponent]
    });
    fixture = TestBed.createComponent(NotificationDailogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
