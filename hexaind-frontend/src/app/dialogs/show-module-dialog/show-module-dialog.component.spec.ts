import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShowModuleDialogComponent } from './show-module-dialog.component';

describe('ShowModuleDialogComponent', () => {
  let component: ShowModuleDialogComponent;
  let fixture: ComponentFixture<ShowModuleDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ShowModuleDialogComponent],
    });
    fixture = TestBed.createComponent(ShowModuleDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
