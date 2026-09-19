import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FileEditorDialogComponent } from './file-editor-view-dialog.component';

describe('FileEditorDialogComponent', () => {
  let component: FileEditorDialogComponent;
  let fixture: ComponentFixture<FileEditorDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FileEditorDialogComponent]
    });
    fixture = TestBed.createComponent(FileEditorDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
