import { ComponentFixture, TestBed } from '@angular/core/testing';

import { scrapScenarioComponent } from './scrap-scenarios.component';

describe('scrapScenarioComponent', () => {
  let component: scrapScenarioComponent;
  let fixture: ComponentFixture<scrapScenarioComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [scrapScenarioComponent]
    });
    fixture = TestBed.createComponent(scrapScenarioComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
