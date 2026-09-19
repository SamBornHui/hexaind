import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FilterSelectionConfigComponent } from './filter-selection-config.component';

describe('FilterSelectionConfigComponent', () => {
  let component: FilterSelectionConfigComponent;
  let fixture: ComponentFixture<FilterSelectionConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FilterSelectionConfigComponent]
    });
    fixture = TestBed.createComponent(FilterSelectionConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
