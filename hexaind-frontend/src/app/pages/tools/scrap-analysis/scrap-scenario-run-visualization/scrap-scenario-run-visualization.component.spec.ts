import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScrapRunVizualizationComponent } from './scrap-scenario-run-visualization.component';

describe('ScrapRunVizualizationComponent', () => {
  let component: ScrapRunVizualizationComponent;
  let fixture: ComponentFixture<ScrapRunVizualizationComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ScrapRunVizualizationComponent]
    });
    fixture = TestBed.createComponent(ScrapRunVizualizationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
