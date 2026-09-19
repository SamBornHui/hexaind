import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Uc6Component } from './uc6.component';

describe('Uc6Component', () => {
  let component: Uc6Component;
  let fixture: ComponentFixture<Uc6Component>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [Uc6Component]
    });
    fixture = TestBed.createComponent(Uc6Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
