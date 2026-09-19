import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomCodeConfigComponent } from './custom-code-config.component';

describe('CustomCodeConfigComponent', () => {
  let component: CustomCodeConfigComponent;
  let fixture: ComponentFixture<CustomCodeConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CustomCodeConfigComponent]
    });
    fixture = TestBed.createComponent(CustomCodeConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
