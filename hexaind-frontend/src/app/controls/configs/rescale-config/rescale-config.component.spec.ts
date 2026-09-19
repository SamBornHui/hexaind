import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RescaleConfigComponent } from './rescale-config.component';

describe('LgbmConfigComponent', () => {
  let component: RescaleConfigComponent;
  let fixture: ComponentFixture<RescaleConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [RescaleConfigComponent]
    });
    fixture = TestBed.createComponent(RescaleConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
