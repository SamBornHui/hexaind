import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NnTorchMlConfigComponent } from './nntorch-ml-config.component';

describe('GBMMlConfigComponent', () => {
  let component: NnTorchMlConfigComponent;
  let fixture: ComponentFixture<NnTorchMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [NnTorchMlConfigComponent],
    });
    fixture = TestBed.createComponent(NnTorchMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
