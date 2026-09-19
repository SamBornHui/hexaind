import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PythonConfigComponent } from './python-config.component';

describe('PythonConfigComponent', () => {
  let component: PythonConfigComponent;
  let fixture: ComponentFixture<PythonConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PythonConfigComponent]
    });
    fixture = TestBed.createComponent(PythonConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
