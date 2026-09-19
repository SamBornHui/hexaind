import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmationPrompComponent } from './confirmation-promp.component';

describe('ConfirmationPrompComponent', () => {
  let component: ConfirmationPrompComponent;
  let fixture: ComponentFixture<ConfirmationPrompComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConfirmationPrompComponent]
    });
    fixture = TestBed.createComponent(ConfirmationPrompComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
