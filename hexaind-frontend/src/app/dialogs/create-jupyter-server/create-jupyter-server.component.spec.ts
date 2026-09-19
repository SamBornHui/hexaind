import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateJupyterServer } from 'src/app/dialogs/create-jupyter-server/create-jupyter-server.component';

describe('CreateNewProjectComponent', () => {
  let component: CreateJupyterServer;
  let fixture: ComponentFixture<CreateJupyterServer>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CreateJupyterServer]
    });
    fixture = TestBed.createComponent(CreateJupyterServer);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
