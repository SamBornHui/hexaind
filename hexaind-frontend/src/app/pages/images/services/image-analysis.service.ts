import { Injectable } from '@angular/core';
import {
  HttpClient,
  HttpHeaders,
  HttpErrorResponse,
} from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Utils } from 'src/app/utils';
import { catchError, map, tap } from 'rxjs/operators';
import { BehaviorSubject, forkJoin, Observable, of, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ImageAnalysisService {
  saveWorkflowBtnChange: Subject<any> = new Subject<any>();
  closeManageWorkflowChange: Subject<any> = new Subject<any>();

  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private sharedDataService: SharedDataService,
  ) { }
  returnKeysFromObject(inpObj: any) {
    return Object.keys(inpObj);
  }

  async getCategorizationData(datasetId: string) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/categorization_data/dataset/${datasetId}`;
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

  getIndividualImageContent(file: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    if (!file.name || file.name.trim() === '') {
      file.name = file.path.split('/').pop();
    }
    let reqData = { 'file_path': file.path, 'file_name': file.name }
    return this.http
      .post(
        url,
        reqData,
        { observe: 'response', responseType: 'blob' },
      )
      .pipe(
        map((response) => {
          if (response.body) {
            const objectURL = URL.createObjectURL(response.body);
            return objectURL;
          } else {
            return null;
          }
        }),
        catchError((error) => {
          return of(null);
        }),
      );
  }

  triggerSaveWorkfloBtn(type: any) {
    this.saveWorkflowBtnChange.next(type);
  }

  triggerCloseManageWorkflow(type: any) {
    this.closeManageWorkflowChange.next(type);
  }
  async getCroppedAndSegmentedImage(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/segmentation`;
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

  async saveWorkflow(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/create_image_workflow`;
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

  async assignWorflowToImages(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/assign_workflow_to_image`;
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

  async getAllWorkflows(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/get_image_workflows`;
      let response = await this.http.get<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async applyWorkflows(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/start_batch_processing`;
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

  async applyRotation(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/rotate_image`;
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

  async updateFoldersStatus(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/workflow_and_batch_status`;
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

  async getCroppedImages(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/update_crop_image`;
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

  async getfoldersImages(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/get_folders_images`;
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

  async removeWorkflowForImage(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/deassociate_workflow_from_image`;
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

  async deleteWorkflow(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/delete_image_workflow`;
      let response = await this.http
        .delete<any>(url, { body: payload })
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }
  async updateFavoriteWorkflow(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/Update_favorite_workflow`;
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

  async updateOutputDirectory(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/update_output_path`;
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

  async checkOutputDirectory(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/check_output_directory`;
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

  async getScalebarForModifiedImage(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/extract_scalebar_value`;
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

  async getMaskImage(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/mask_image`;
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

  async saveScalebar(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/save_scalebar_value`;
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

  async applyCropImage(payload: any) {
    try {
      payload['user_id'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/crop_image`;
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

  exploreAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/exploreAnalysis', data, {
      headers: headers,
    });
  }

  performAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performAnalysis', data, {
      headers: headers,
    });
  }

  performProfileAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performProfileAnalysis', data, {
      headers: headers,
    });
  }

  performMetalRecessAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performMetalRecessAnalysis', data, {
      headers: headers,
    });
  }

  performTierAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performTierAnalysis', data, {
      headers: headers,
    });
  }

  performBubbleAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performBubbleAnalysis', data, {
      headers: headers,
    });
  }

  performPillarAnomalyAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performPillarAnomalyAnalysis', data, {
      headers: headers,
    });
  }

  performPillarC2cAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performPillarC2cAnalysis', data, {
      headers: headers,
    });
  }

  performMetalVoidsAnalysis(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    data['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/performMetalVoidsAnalysis', data, {
      headers: headers,
    });
  }

  getAutoCropValue(imageData: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    imageData['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/getAutoCropValue', imageData, {
      headers: headers,
    });
  }

  deleteUnusedWfImages(imageData: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    imageData['userId'] = localStorage.getItem('currUserID');
    return this.http.post('/imageAnalysis/deleteUnusedWfImages', imageData, {
      headers: headers,
    });
  }

  updateLastAccess(data: any): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    return this.http.put('/dataManagement/lastModifiedUpdate', data, {
      headers: headers,
    });
  }
  disassociateWorkflowBatch(
    imagesList: any[],
    workflowId: string,
  ): Observable<any> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    var requests = imagesList.map((image) => {
      let apiUrl = '/imageAnalysis/DissociateWorkflowFromImage';
      return this.http
        .post(
          apiUrl,
          {
            path: image.path,
            wid: workflowId,
            userId: localStorage.getItem('currUserID'),
          },
          { headers: headers },
        )
        .pipe(
          map((response) => response),
          catchError((error) => {
            return error;
          }),
          tap(() => { }),
        );
    });
    return forkJoin(requests);
  }

  async createImageMasking(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/save_mask`;
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

  async deleteImageMasking(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/delete_masked_objs`;
      let response = await this.http.delete<any>(url, { body: payload }).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getImageMasking(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/get_masked_objs`;
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

  async updateImageMasking(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/update_mask`;
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

  async resetImage(payload: any) {
    try {
      let url = `${this.configService.getImageAnalysisUrl()}/reset_manual_image`;
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

  async segmentedImagePath(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/workflow_images_path`;
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

}
