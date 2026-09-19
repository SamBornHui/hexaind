import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EnlargedTextEditorComponent } from './enlarged-text-editor.component';

describe('EnlargedTextEditorComponent', () => {
  let component: EnlargedTextEditorComponent;
  let fixture: ComponentFixture<EnlargedTextEditorComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EnlargedTextEditorComponent]
    });
    fixture = TestBed.createComponent(EnlargedTextEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
