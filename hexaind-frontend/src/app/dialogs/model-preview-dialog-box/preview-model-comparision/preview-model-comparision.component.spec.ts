import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PreviewModelComparisionComponent } from './preview-model-comparision.component';

describe('PreviewModelComparisionComponent', () => {
  let component: PreviewModelComparisionComponent;
  let fixture: ComponentFixture<PreviewModelComparisionComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PreviewModelComparisionComponent]
    });
    fixture = TestBed.createComponent(PreviewModelComparisionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
