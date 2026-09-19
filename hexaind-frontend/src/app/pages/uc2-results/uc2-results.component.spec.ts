import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Uc2ResultsComponent } from './uc2-results.component';

describe('Uc2ResultsComponent', () => {
  let component: Uc2ResultsComponent;
  let fixture: ComponentFixture<Uc2ResultsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [Uc2ResultsComponent]
    });
    fixture = TestBed.createComponent(Uc2ResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
