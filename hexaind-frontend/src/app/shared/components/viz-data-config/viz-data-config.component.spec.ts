/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VizDataConfigComponent } from './viz-data-config.component';

describe('VizDataConfigComponent', () => {
  let component: VizDataConfigComponent;
  let fixture: ComponentFixture<VizDataConfigComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [VizDataConfigComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VizDataConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
