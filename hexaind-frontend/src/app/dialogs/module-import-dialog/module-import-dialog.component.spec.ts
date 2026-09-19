import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModuleImportDialogComponent } from './module-import-dialog.component';

describe('ModuleImportDialogComponent', () => {
  let component: ModuleImportDialogComponent;
  let fixture: ComponentFixture<ModuleImportDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ModuleImportDialogComponent]
    });
    fixture = TestBed.createComponent(ModuleImportDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
