import { ComponentFixture, TestBed } from '@angular/core/testing';

import { JupyterConfigComponent } from './jupyter-data-config.component';

describe('JupyterConfigComponent', () => {
  let component: JupyterConfigComponent;
  let fixture: ComponentFixture<JupyterConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [JupyterConfigComponent]
    });
    fixture = TestBed.createComponent(JupyterConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
