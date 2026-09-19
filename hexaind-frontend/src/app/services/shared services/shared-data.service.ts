// src/app/shared-data.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class SharedDataService {
  private rescaleDatasetIds = new Map<string, string>();
  [x: string]: any;
  // The last error reported.
  private _lastError = new BehaviorSubject<string | null>(null);
  lastError$ = this._lastError.asObservable();

  private _enableCanvas = new Subject<any>;
  enableCanvas$ = this._enableCanvas.asObservable()
  set LastError(value: string | null) {
    this._lastError.next(value);
  }

  get LastError(): string | null {
    return this._lastError.getValue();
  }

  // Our role ID.
  private _roleId = new BehaviorSubject<string | null>(null);
  roleId$ = this._lastError.asObservable();

  set RoleId(value: string | null) {
    this._roleId.next(value);
  }

  get RoleId(): string | null {
    return this._roleId.getValue();
  }

  // Set rescale dataset ID in Map and localStorage for a specific widget URN
  setRescaleDatasetId(widgetUrn: string, datasetId: string) {
    this.rescaleDatasetIds.set(widgetUrn, datasetId);
    localStorage.setItem(`rescaleDatasetId_${widgetUrn}`, datasetId);
  }

  // Get rescale dataset ID for a specific widget URN, checking Map and localStorage
  getRescaleDatasetId(widgetUrn: string): string | undefined {
    const datasetId = this.rescaleDatasetIds.get(widgetUrn);
    if (!datasetId) {
      return localStorage.getItem(`rescaleDatasetId_${widgetUrn}`) || undefined;
    }
    return datasetId;
  }

  // Clear rescale dataset ID for a specific widget URN from Map and localStorage
  clearRescaleDatasetId(widgetUrn: string) {
    this.rescaleDatasetIds.delete(widgetUrn);
    localStorage.removeItem(`rescaleDatasetId_${widgetUrn}`);
  }

  disableCanvas() {
    this._enableCanvas.next(false)
  }

  enableCanvas() {
    this._enableCanvas.next(true)
  }

}
