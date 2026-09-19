import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Utils } from 'src/app/utils';
import { catchError, map, tap } from 'rxjs/operators';
import { BehaviorSubject, forkJoin, Observable, of, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ImageAnnotationService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private sharedDataService: SharedDataService
  ) { }

  returnKeysFromObject(inpObj: any) {
    return Object.keys(inpObj);
  }

  async deleteAnnotation(annotationId: string) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/delete_annotation/${annotationId}`;
      let response = await this.http.delete<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getSavedAnnotationsByDatasetId(datasetId: string) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/dataset/${datasetId}/get_saved_annotations`;
      let response = await this.http.post<any>(url, {}).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async saveAnnotations(reqObj: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/save_annotations`;
      let response = await this.http.post<any>(url, { annotations: reqObj }).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async changeAnnotationName(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/change_annotation_name`;
      let response = await this.http.put<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async changeAnnotationLabel(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/change_annotation_label`;
      let response = await this.http.put<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async updateCoordinatesOfCanvas(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/update_coordinates`;
      let response = await this.http.put<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getSegmentedAnnotations(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/generate_interactive_segmeneted_image`;
      let response = await this.http.post<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async updateSegmentedImageAnnotations(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/update_image_annotations`;
      let response = await this.http.post<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getDistinctLabels() {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/get_all_unique_segmentation_labels`;
      let response = await this.http.post<any>(url, {}).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async generateSegmenationTabularDataset(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/generate_segmenation_tabular_dataset`;
      let response = await this.http.post<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  getPrefixDataset(projectId: any) {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    return this.http.get('/dataManagement/getDatasetPrefix/' + projectId, { headers: headers });
  }

  async deleteSegmentedImageAnnotation(payload: any) {
    try {
      const url = `${this.configService.getImageAnalysisUrl()}/delete_segment_annotation`;
      const options = {
        body: payload,
      };
      const response = await this.http.delete<any>(url, options).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async deleteSegmentedImageAnnotationLabel(payload: any) {
    try {
      const url = `${this.configService.getImageAnalysisUrl()}/delete_label/${payload['label_name']}`;
      const options = {
        body: payload,
      };
      const response = await this.http.delete<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

}
