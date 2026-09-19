import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdvanceSearchSigmaComponent } from './advance-search-sigma.component';

describe('AdvanceSearchComponent', () => {
  let component: AdvanceSearchSigmaComponent;
  let fixture: ComponentFixture<AdvanceSearchSigmaComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AdvanceSearchSigmaComponent]
    });
    fixture = TestBed.createComponent(AdvanceSearchSigmaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
