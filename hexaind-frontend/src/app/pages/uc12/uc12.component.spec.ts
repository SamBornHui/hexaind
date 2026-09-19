import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Uc12Component } from './uc12.component';

describe('Uc12Component', () => {
  let component: Uc12Component;
  let fixture: ComponentFixture<Uc12Component>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [Uc12Component]
    });
    fixture = TestBed.createComponent(Uc12Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
