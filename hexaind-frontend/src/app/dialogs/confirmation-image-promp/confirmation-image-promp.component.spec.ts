import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmationImagePrompComponent } from './confirmation-image-promp.component';

describe('ConfirmationImagePrompComponent', () => {
  let component: ConfirmationImagePrompComponent;
  let fixture: ComponentFixture<ConfirmationImagePrompComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConfirmationImagePrompComponent]
    });
    fixture = TestBed.createComponent(ConfirmationImagePrompComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
