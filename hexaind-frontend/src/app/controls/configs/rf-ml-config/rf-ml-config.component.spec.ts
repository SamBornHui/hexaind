import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RfMlConfigComponent } from './rf-ml-config.component';

describe('RfMlConfigComponent', () => {
  let component: RfMlConfigComponent;
  let fixture: ComponentFixture<RfMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [RfMlConfigComponent]
    });
    fixture = TestBed.createComponent(RfMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
