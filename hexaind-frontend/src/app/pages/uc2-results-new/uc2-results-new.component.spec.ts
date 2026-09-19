import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Uc2ResultsNewComponent } from './uc2-results-new.component';

describe('Uc2ResultsComponent', () => {
  let component: Uc2ResultsNewComponent;
  let fixture: ComponentFixture<Uc2ResultsNewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [Uc2ResultsNewComponent]
    });
    fixture = TestBed.createComponent(Uc2ResultsNewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
