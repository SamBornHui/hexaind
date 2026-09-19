import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MoboConfigComponent } from './mobo-config.component';

describe('MoboConfigComponent', () => {
  let component: MoboConfigComponent;
  let fixture: ComponentFixture<MoboConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MoboConfigComponent]
    });
    fixture = TestBed.createComponent(MoboConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
