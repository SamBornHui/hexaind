import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GprConfigComponent } from './gpr-config.component';

describe('GprConfigComponent', () => {
  let component: GprConfigComponent;
  let fixture: ComponentFixture<GprConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GprConfigComponent]
    });
    fixture = TestBed.createComponent(GprConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
