import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SvmConfigComponent } from './svm-config.component';

describe('SvmConfigComponent', () => {
  let component: SvmConfigComponent;
  let fixture: ComponentFixture<SvmConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SvmConfigComponent]
    });
    fixture = TestBed.createComponent(SvmConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
