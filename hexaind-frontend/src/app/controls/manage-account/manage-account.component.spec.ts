import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageAccountComponent } from './manage-account.component';

describe('MyModelComponent', () => {
  let component: ManageAccountComponent;
  let fixture: ComponentFixture<ManageAccountComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ManageAccountComponent]
    });
    fixture = TestBed.createComponent(ManageAccountComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
