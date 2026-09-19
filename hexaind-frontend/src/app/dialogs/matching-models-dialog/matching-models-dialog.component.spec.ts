import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MatchingModelsDialogComponent } from './matching-models-dialog.component';

describe('MatchingModelsDialogComponent', () => {
  let component: MatchingModelsDialogComponent;
  let fixture: ComponentFixture<MatchingModelsDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MatchingModelsDialogComponent],
    });
    fixture = TestBed.createComponent(MatchingModelsDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
