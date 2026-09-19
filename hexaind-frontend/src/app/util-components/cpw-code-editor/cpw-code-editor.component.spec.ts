import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CpwCodeEditorComponent } from './cpw-code-editor.component';

describe('CpwCodeEditorComponent', () => {
  let component: CpwCodeEditorComponent;
  let fixture: ComponentFixture<CpwCodeEditorComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CpwCodeEditorComponent]
    });
    fixture = TestBed.createComponent(CpwCodeEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
