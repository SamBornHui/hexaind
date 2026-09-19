import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Connector, ConnectorListResponse } from 'src/app/models/connector-models';
import { ConfigService } from 'src/app/services/config.service';

@Injectable({
  providedIn: 'root',
})
export class WorkflowDesignerServiceService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  private triggerSaveSubject = new BehaviorSubject<boolean>(false);
  triggerSave$ = this.triggerSaveSubject.asObservable();
  
  private triggerExecuteWidgetSubject = new BehaviorSubject<boolean>(false);
  triggerExecuteWidget$ = this.triggerExecuteWidgetSubject.asObservable();

  private triggerMonitorRunSubject = new BehaviorSubject<boolean>(false);
  triggerMonitorRun$ = this.triggerMonitorRunSubject.asObservable();

  setTriggerSave(value: boolean) {
    this.triggerSaveSubject.next(value);
  }

  setTriggerExecuteWidget(value: boolean) {
    this.triggerExecuteWidgetSubject.next(value);
  }

  private saveTriggeredFrom = "";

  getSaveTriggeredFrom() {
    return this.saveTriggeredFrom;
  }

  setSaveTriggeredFrom(from: string) {
    this.saveTriggeredFrom = from;
  }

  setTriggerMonitorRun(value: boolean) {
    this.triggerMonitorRunSubject.next(value);
  }
}
