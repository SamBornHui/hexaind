import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScrapRunsComponent } from './scrap-runs.component';

describe('ScrapRunsComponent', () => {
  let component: ScrapRunsComponent;
  let fixture: ComponentFixture<ScrapRunsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ScrapRunsComponent]
    });
    fixture = TestBed.createComponent(ScrapRunsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
