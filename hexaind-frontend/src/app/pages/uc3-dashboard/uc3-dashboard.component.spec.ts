import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Uc3DashboardComponent } from './uc3-dashboard.component';

describe('Uc3DashboardComponent', () => {
  let component: Uc3DashboardComponent;
  let fixture: ComponentFixture<Uc3DashboardComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [Uc3DashboardComponent]
    });
    fixture = TestBed.createComponent(Uc3DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
