import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Uc3ProbeModelPopupComponent } from './uc3-probe-model-popup.component';

describe('Uc3ProbeModelPopupComponent', () => {
  let component: Uc3ProbeModelPopupComponent;
  let fixture: ComponentFixture<Uc3ProbeModelPopupComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [Uc3ProbeModelPopupComponent]
    });
    fixture = TestBed.createComponent(Uc3ProbeModelPopupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
