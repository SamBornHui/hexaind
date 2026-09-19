import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MprConfigComponent } from './mpr-config.component';

describe('MprConfigComponent', () => {
  let component: MprConfigComponent;
  let fixture: ComponentFixture<MprConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MprConfigComponent]
    });
    fixture = TestBed.createComponent(MprConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
