import { TestBed } from '@angular/core/testing';

import { JupyterNotebookService } from './jupyter-notebook.service';

describe('JupyterNotebookService', () => {
  let service: JupyterNotebookService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(JupyterNotebookService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
