import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SigmaCommonTestComponent } from './sigma-common-test.component';

describe('SigmaCommonTestComponent', () => {
  let component: SigmaCommonTestComponent;
  let fixture: ComponentFixture<SigmaCommonTestComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SigmaCommonTestComponent]
    });
    fixture = TestBed.createComponent(SigmaCommonTestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
