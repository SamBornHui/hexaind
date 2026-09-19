import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LGBMMlConfigComponent } from './lgbm-ml-config.component';

describe('GBMMlConfigComponent', () => {
  let component: LGBMMlConfigComponent;
  let fixture: ComponentFixture<LGBMMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [LGBMMlConfigComponent],
    });
    fixture = TestBed.createComponent(LGBMMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
