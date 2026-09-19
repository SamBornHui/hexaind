import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CopyPasswordComponent } from './copy-password.component';

describe('CopyPasswordComponent', () => {
  let component: CopyPasswordComponent;
  let fixture: ComponentFixture<CopyPasswordComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CopyPasswordComponent]
    });
    fixture = TestBed.createComponent(CopyPasswordComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
