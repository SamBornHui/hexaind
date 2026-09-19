import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ConfigService } from '../../../services/config.service';
import { BehaviorSubject, catchError, interval, Observable, of, Subject, Subscription, switchMap, takeUntil, takeWhile } from 'rxjs';

interface GetStatisticsAndSchemaResponse {
  column_names: string[];
  row_names: string[];
  total_number_of_rows: number
}

export interface GetDataResponse {
  column_names: string[];
  row_names: string[];
  rows: string[]
}

interface GetMetadataResponse {
  name: string;
  data_source: string;
  description: string;
  dataset_id: string
}

interface GetVisualizationResponse {
  filepath: string
}

@Injectable({
  providedIn: 'root'
})
export class DataPreviewService implements OnDestroy {
  [x: string]: any;
  private numericalColumnNamesSubject = new BehaviorSubject<string[]>([]);
  private categoricalColumnNamesSubject = new BehaviorSubject<string[]>([]);
  private numericalDataSourceSubject = new BehaviorSubject<string[]>([]);

  constructor(private http: HttpClient,
    private configService: ConfigService,) { }

  numericalStatisticsSubscription: Subscription | null = null;
  categoricalStatisticsSubscription: Subscription | null = null;
  POLLING_INTERVAL = 5000;

  ngOnDestroy(){
    this.unsubscribeNumerical();
    this.unsubscribeCategorical();
  }

  private cancelNumericalPolling$ = new Subject<void>();
  private cancelCategoricalPolling$ = new Subject<void>();

  async loadNumericalData(dataset_id: string, numericalPage?: number, numericalPageSize?: number): Promise<any> {
    try {
      const response = await this.getNumericalStatistics(dataset_id, numericalPage, numericalPageSize);
      
      if (response) {
        if (response.statistics) {
          return response; 
        } else if (response.api_job_id) {
          return await this.pollForNumericalStatistics(dataset_id, numericalPage, numericalPageSize);
        }
      }
      return response; 
    } catch (error) {
      console.error("Error:", error);
      throw error; 
    }
  }

  pollForNumericalStatistics(dataset_id: string, numericalPage?: number, numericalPageSize?: number): Promise<any> {
    return new Promise((resolve, reject) => {
      this.numericalStatisticsSubscription = interval(this.POLLING_INTERVAL)
        .pipe(
          switchMap(() => this.getNumericalStatistics(dataset_id, numericalPage, numericalPageSize)),
          takeWhile(response => response && !response.statistics, true),
          takeUntil(this.cancelNumericalPolling$),
          catchError(error => {
            console.error('Error during polling:', error);
            this.unsubscribeNumerical();
            reject(error);
            return of(null);
          })
        )
        .subscribe(response => {
          if (response.statistics) resolve(response);
        });
      
      this.cancelCategoricalPolling$.subscribe(() => {
          reject(new Error('Polling was canceled.'));
      });
    });
  }

  async loadCategoricalData(dataset_id: string, categoricalPage?: number, categoricalPageSize?: number): Promise<any> {
    try {
      const response = await this.getCategoricalStatistics(dataset_id, categoricalPage, categoricalPageSize);
      
      if (response) {
        if (response.statistics) {
          return response; 
        } else if (response.api_job_id) {
          return await this.pollForCategoricalStatistics(dataset_id, categoricalPage, categoricalPageSize);
        }
      }
      return response; 
    } catch (error) {
      console.error("Error:", error);
      throw error; 
    }
  }

  pollForCategoricalStatistics(dataset_id: string, categoricalPage?: number, categoricalPageSize?: number): Promise<any> {

    return new Promise((resolve, reject) => {
      this.categoricalStatisticsSubscription = interval(this.POLLING_INTERVAL)
        .pipe(
          switchMap(() => this.getCategoricalStatistics(dataset_id, categoricalPage, categoricalPageSize)),
          takeWhile(response => response && !response.statistics, true),
          takeUntil(this.cancelCategoricalPolling$),
          catchError(error => {
            console.error('Error during polling:', error);
            this.unsubscribeCategorical();
            reject(error);
            return of(null);
          })
        )
        .subscribe(response => {
          if (response.statistics) resolve(response);
        });
      
      this.cancelCategoricalPolling$.subscribe(() => {
          reject(new Error('Polling was canceled.'));
      });
    });
  }

  unsubscribeNumerical() {
    this.cancelNumericalPolling$.next(); 
    this.cancelNumericalPolling$.complete();
    this.cancelNumericalPolling$ = new Subject<void>();
    this.numericalStatisticsSubscription?.unsubscribe();
  }

  unsubscribeCategorical() {
    this.cancelCategoricalPolling$.next(); 
    this.cancelCategoricalPolling$.complete();
    this.cancelCategoricalPolling$ = new Subject<void>();
    this.categoricalStatisticsSubscription?.unsubscribe();
  }

  getNumericalColumnNamesObservable() {
    return this.numericalColumnNamesSubject.asObservable();
  }

  updateNumericalColumnNames(newColumnNames: string[]) {
    this.numericalColumnNamesSubject.next(newColumnNames);
  }

  getCategoricalColumnNamesObservable() {
    return this.categoricalColumnNamesSubject.asObservable();
  }

  updateCategoricalColumnNames(newColumnNames: string[]) {
    this.categoricalColumnNamesSubject.next(newColumnNames);
  }

  getNumericalDataSourceObservable() {
    return this.numericalDataSourceSubject.asObservable();
  }

  updateNumericalDataSource(newColumnNames: any[]) {
    this.numericalDataSourceSubject.next(newColumnNames);
  }

  async getStatisticsAndSchema(dataset_id: string): Promise<any | undefined> {
    try {
      const url: string = `${this.configService.getAppAuxApiURL}/eda/statistics?dataset_id=${dataset_id}`;
      const response = await this.http.get<GetStatisticsAndSchemaResponse>(url).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  async getNumericalStatistics(dataset_id: string, page?: number, pageSize?: number): Promise<any | undefined> {
    try {
      let url: string = `${this.configService.getAppAuxApiURL}/eda/statistics_numerical?dataset_id=${dataset_id}`;
      if (page !== undefined) {
        url += `&page=${page}`;
      }

      if (pageSize !== undefined) {
        url += `&page_size=${pageSize}`;
      }
      const response = await this.http.get<GetStatisticsAndSchemaResponse>(url).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  async getCategoricalStatistics(dataset_id: string, page?: number, pageSize?: number): Promise<any | undefined> {
    try {
      let url: string = `${this.configService.getAppAuxApiURL}/eda/statistics_categorical?dataset_id=${dataset_id}`;
      
      if (page !== undefined) {
        url += `&page=${page}`;
      }
      
      if (pageSize !== undefined) {
        url += `&page_size=${pageSize}`;
      }
      const response = await this.http.get<GetStatisticsAndSchemaResponse>(url).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }
  async getData(dataset_id: string, page: number, pageSize: number): Promise<any | undefined> {
    try {
      const url: string = `${this.configService.getAppAuxApiURL}/eda/preview?dataset_id=${dataset_id}&page=${page}&page_size=${pageSize}`;
      const response = await this.http.get<GetDataResponse>(url).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  async getVisualization(dataset_id: string, xAxis: string, yAxis: string, selectedPlotType: string, interactive: boolean, color_by: string, additional_config?: any): Promise<string | undefined> {
    const body = {
      "color_by": color_by != '' ? color_by : null,
      "plot_type": selectedPlotType,
      "version": "1.0",
      "x": xAxis,
      "y": yAxis,
      ...(additional_config && Object.keys(additional_config).length > 0 ? { "additional_config": additional_config} : {})
    }
    
    try {
      let query = `dataset_id=${dataset_id}&interactive=${interactive}`;
      const url: string = `${this.configService.getAppAuxApiURL}/eda/visualization?${query}`;
      const response = await this.http.post<GetVisualizationResponse>(url, body).toPromise();
      return response?.filepath
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  async getMetadata(dataset_id: string): Promise<any | undefined> {
    try {
      const url: string = `${this.configService.getAppAuxApiURL}/eda/metadata?dataset_id=${dataset_id}`;
      const response = await this.http.get<GetMetadataResponse>(url).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  async getCorrelationHeatmap(dataset_id: string, columns: string[], additional_config: any): Promise<any> {
    const body = {
      "dataset_id": dataset_id,
      "columns": columns,
      ...additional_config
    }
    try {
      const url: string = `${this.configService.getAppAuxApiURL}/eda/correlation_heatmap`;
      const response = await this.http.post(url, body).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  async renameColumn(dataset_id: string, data: any): Promise<any> {
    try {
      const url: string = `${this.configService.getAppAuxApiURL}/eda/columns?dataset_id=${dataset_id}`;
      const response = await this.http.patch(url, data).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

  downloadVisualization(
    trials:any
  ): Observable<any> {
    const url: string = `${this.configService.getAppApiURL}/assets/download_viz_data`;
    return this.http.post(
      url,
      trials,
      {
        responseType: 'blob',
      },
    );
  }
}
