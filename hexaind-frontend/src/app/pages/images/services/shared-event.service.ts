// shared.service.ts
import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class SharedImageAnnotationEventService {
  private buttonClickSource = new Subject<void>();

  buttonClick$ = this.buttonClickSource.asObservable();

  triggerSaveAsButtonClick() {
    this.buttonClickSource.next();
  }
}