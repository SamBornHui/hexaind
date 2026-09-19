import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GaussianProcessClassificationConfigComponent } from './gaussian-process-classification-config.component';

describe('GaussianProcessClassificationConfigComponent', () => {
  let component: GaussianProcessClassificationConfigComponent;
  let fixture: ComponentFixture<GaussianProcessClassificationConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GaussianProcessClassificationConfigComponent]
    });
    fixture = TestBed.createComponent(GaussianProcessClassificationConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
