import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InjestionDialogComponent } from './injestion-dialog.component';

describe('InjestionDialogComponent', () => {
  let component: InjestionDialogComponent;
  let fixture: ComponentFixture<InjestionDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [InjestionDialogComponent]
    });
    fixture = TestBed.createComponent(InjestionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
