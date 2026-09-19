import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ConfigService } from '../../../services/config.service';

@Injectable({
  providedIn: 'root'
})
export class DataVisualizationService {
  constructor(private http: HttpClient,
    private configService: ConfigService
  ) { }

  async getVizualizationDataResult(dataset_id: string): Promise<any | undefined> {
    try {
      const url: string = `${this.configService.getAppAuxApiURL}/eda/statistics?dataset_id=${dataset_id}`;
      const response = await this.http.get<any>(url).toPromise();
      return response
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        throw new Error(error.error.detail.message)
      }
      throw new Error('Something bad happened; please try again later.');
    }
  }

}
