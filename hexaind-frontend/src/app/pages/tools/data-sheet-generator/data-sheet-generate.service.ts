import { HttpClient, HttpErrorResponse, HttpEvent, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, lastValueFrom, map, Observable, of } from 'rxjs';
import { Utils } from 'src/app/utils';
import { environment } from 'src/environments/environment';
@Injectable({
  providedIn: 'root',
})
export class DataSheetGenerateService {
  constructor(private http: HttpClient) { }

  private activityLogData: any;

  setActivityLogData(data: any): void {
    this.activityLogData = data;
  }

  getActivityLogData(): any {
    return this.activityLogData;
  }

  getDatasheet(
    siteId: number,
    projectId: string,
    datasheetId: number,
    nominalAge: number,
    reset: boolean,
  ): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/datasheet/${datasheetId}/nominal_age/${nominalAge}/reset/${reset}/`;
    return this.http.post<any>(url, {});
  }

  async saveMetadata(siteId: string, projectId: string, datasheet: string, jsonData: Record<string, any>): Promise<any> {
    const url: string = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/datasheet/${datasheet}/save_metadata`;
    try {
      const response = await lastValueFrom(this.http.post<any>(url, jsonData));
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  generateDataSheet(
    siteId: number,
    projectId: string,
    datasheetId: number,
    nominalAge: number,
    JsonData: object,
    fit_type: string,
  ): Observable<any> {
    let url: string;
    if (fit_type == 'initial') {
      url = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/generate_datasheet/${datasheetId}/nominal_age/${nominalAge}/`;
    } else {
      url = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/generate_new_datasheet/${datasheetId}/nominal_age/${nominalAge}/`;
    }
    return this.http.post<any>(url, JsonData);
  }

  ingestData(
    formData: FormData,
    siteId: string,
    projectId: string,
  ): Observable<HttpEvent<any>> {
    const url = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/datasheet/ingest_data`;
    return this.http.post<any>(url, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }

  readCSV(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/datasheet/read_csv`;
    return this.http.post<any>(url, JsonData).pipe(
      catchError((error) => {
        return of({ csv_data: [] });
      }),
      map((response) => {
        if (
          response.csv_data &&
          response.csv_data.length === 1 &&
          Object.keys(response.csv_data[0]).length === 0
        ) {
          return { csv_data: [] };
        }
        return response;
      }),
    );
  }

  previewDatasheet(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/datasheet/preview`;
    return this.http.post<any>(url, JsonData);
  }

  downloadDatasheet(projectId: string, datasheet: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/${datasheet}/download_results`;
    return this.http.post(
      url,
      {},
      {
        responseType: 'blob',
      },
    );
  }

  computeElasticModule(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/datasheet/correct_tensile`;
    return this.http.post<any>(url, JsonData);
  }

  computeLocalFit(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/datasheet/local_fit`;
    return this.http.post<any>(url, JsonData);
  }

  getDataSheetNumber(jsonData: object, projectId: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/get_datasheets`;
    return this.http.post<any>(url, jsonData);
  }

  getNominalAge(jsonData: object, projectId: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/get_datasheets`;
    return this.http.post<any>(url, jsonData);
  }

  saveFLCAscii(jsonData: object, projectId: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/save_flc_ascii`;
    return this.http.post<any>(url, jsonData);
  }

  uploadFileToConvert(
    projectId: string,
    formData: FormData,
    metadataFileName: string,
  ): Observable<any> {
    const encodedFileName = encodeURIComponent(metadataFileName);
    const url = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/upload_flc_file_to_convert?metadataFile=${encodedFileName}`;
    return this.http.post<any>(url, formData);
  }

  uploadTensileFileToConvert(
    projectId: string,
    formData: FormData,
  ): Observable<HttpEvent<any>> {
    const url = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/upload_tensile_file_to_convert`;
    return this.http.post<any>(url, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }

  tensileFileConvert(jsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/datasheet/tensile_file_convertor`;
    return this.http.post<any>(url, jsonData);
  }

  saveTensileAscii(jsonData: object, projectId: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/save_tensile_ascii`;
    return this.http.post<any>(url, jsonData);
  }

  downloadAscii(
    projectId: string,
    datasheet: string,
    nominalAge: string,
    fileType: string,
  ): Observable<any> {
    const url = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/download_ascii?datasheet=${datasheet}&nominal_age=${nominalAge}&file_type=${fileType}`;
    return this.http.post(
      url,
      {},
      {
        responseType: 'blob',
      },
    );
  }

  getDatasheetDetails(jsonData: object, projectId: string): Observable<any> {
    const url = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/get_datasheets_details`;
    return this.http.post<any>(url, jsonData);
  }

  async deleteDatasheet(projectId: string, folderPath: string): Promise<any> {
    try {
      const url = `${environment.apiUrl}/v1/sites/projects/${projectId}/datasheet/${encodeURIComponent(folderPath)}/delete`;
      const response = await this.http.delete<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  async downloadFolder(projectId: string, path: string): Promise<Blob> {
    try {
      const url = `${environment.apiUrl}/v1/sites/1/projects/${projectId}/datasheet/download_file`;
      const body = { path };
      const response = await this.http.post(url, body, { responseType: 'blob' }).toPromise();

      if (!response) {
        throw new Error('The server did not return a valid file.');
      }

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }



  async saveChanges(
    siteId: string,
    projectId: string,
    datasheetId: number,
    nominalAge: number,
    selectedDataSheetId: string,
    jsonData: object
  ): Promise<any> {
    const payload = { data: jsonData };

    const url: string = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/datasheet/${datasheetId}/nominal_age/${nominalAge}/selected_datasheet/${selectedDataSheetId}/save_changes`;

    return new Promise((resolve, reject) => {
      this.http.post<any>(url, payload).subscribe({
        next: (response) => resolve(response),
        error: (err) => {
          console.error('Error saving changes:', err);
          reject(err);
        },
      });
    });
  }

  async updateDatasheet(datasheetId: string, updatedDatasheet: any): Promise<any> {
    try {
      const url: string = `${environment.apiUrl}/v1/sites/datasheet/update_datasheet/${datasheetId}`;
      const response = await this.http.put<any>(url, updatedDatasheet).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  async setInitialFit(siteId: string, projectId: string, dataSheetId: string, nominalAge: string, jsonData: Record<string, any>): Promise<any> {
    const url = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/set_initial_fit/${dataSheetId}/nominal_age/${nominalAge}`;

    try {
      const response = await lastValueFrom(this.http.post<any>(url, jsonData));
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  async resetCorrectedTensileSample(jsonData: Record<string, any>): Promise<any> {
    const url = `${environment.apiUrl}/v1/sites/datasheet/reset_tensile_sample`;

    try {
      const response = await lastValueFrom(this.http.post<any>(url, jsonData));
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  async comparisonCorrectedTensileSample(jsonData: Record<string, any>): Promise<any> {
    const url = `${environment.apiUrl}/v1/sites/datasheet/comparison_tensile_sample`;

    try {
      const response = await lastValueFrom(this.http.post<any>(url, jsonData));
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        const errorMessage = Utils.GetHttpResponseError(error);
        throw new Error(errorMessage);
      }
      throw error;
    }
  }

  getTensileSampleData(
    siteId: string,
    projectId: string,
    datasheetId: number,
    nominalAge: number,
    jsonData: Record<string, any>
  ): Observable<any> {
    const url = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/datasheet/${datasheetId}/nominal_age/${nominalAge}/tensile_sample_data`;
    return this.http.post<any>(url, jsonData).pipe(
      catchError((error) => {
        console.error('Error fetching tensile sample data:', error);
        return of(null);
      })
    );
  }
}
