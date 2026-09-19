import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScrapAnalysisComponent } from './scrap-analysis.component';

describe('ScrapAnalysisComponent', () => {
  let component: ScrapAnalysisComponent;
  let fixture: ComponentFixture<ScrapAnalysisComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ScrapAnalysisComponent]
    });
    fixture = TestBed.createComponent(ScrapAnalysisComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
