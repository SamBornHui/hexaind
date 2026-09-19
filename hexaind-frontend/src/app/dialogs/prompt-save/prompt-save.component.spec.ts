import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PromptSaveComponent } from './prompt-save.component';

describe('PromptSaveComponent', () => {
  let component: PromptSaveComponent;
  let fixture: ComponentFixture<PromptSaveComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PromptSaveComponent]
    });
    fixture = TestBed.createComponent(PromptSaveComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
