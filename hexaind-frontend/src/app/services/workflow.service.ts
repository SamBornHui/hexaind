// workflow.service.ts

import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class WorkflowService {
  [x: string]: any;
  private saveWorkflowSubject = new Subject<void>();

  saveWorkflow() {
    this.saveWorkflowSubject.next();
  }

  onSaveWorkflow() {
    return this.saveWorkflowSubject.asObservable();
  }
}
