import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import {
  HttpClient,
  HttpEvent,
  HttpRequest,
  HttpHeaders,
  HttpResponse,
} from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { Observable } from 'rxjs/internal/Observable';
import { map } from 'rxjs/operators';
import { lastValueFrom } from 'rxjs';

interface AllSessionsResponse {
  datacatalog_sessions: [];
  total_count: number;
}

interface DataPullStatusResponse {
  current_stage: String;
  current_stage_status: String;
  fd_data_pull_job_status: String;
  job_status: {
    job_stage: String;
    job_stage_status: {
      total_bytes_processed: String;
      total_bytes_billed: String;
      bigquery_job_id: String;
      progress_percentage: number;
      progress_message: String;
    };
  };
}

interface FabDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    facilities: {
      file_path: '';
      selected_values: null;
    };
  };
  total_count: number;
}

interface ToolStatus {
  data: never[];
  tool_name: string;
  tool_id: string;
}

export interface GenerateToolIdsResponse {
  data: ToolStatus[];
}
interface FetchRecipesResponse {
  uniques: string[]; // Assuming 'uniques' is an array of recipe names
  rows_count: number;
}

// Define the structure of your API response
interface GenerateRecipesResponse {
  recipes: {
    file_path: string;
    selected_values: string[] | null;
  };
  tool_ids: {
    file_path: string;
    selected_values: string[] | null;
  };
  step_ids: {
    file_path: string;
    selected_values: string[] | null;
  };
  sensors: {
    file_path: string;
    selected_values: string[] | null;
  };
}

// Interface for the response from the fetchRecipesNamesAndIds method
interface RecipeAPIResponse {
  recipe_name: string; // Adjust this based on your actual response structure
}

interface StepIdSensorResponse {
  sensors: {
    file_path: string;
    selected_values: string[] | null;
  };
  step_ids: {
    file_path: string;
    selected_values: string[] | null;
  };
}

interface StepIdResponse {
  uniques: string[];
  rows_count: number;
}

interface FinalStatus {}

interface TechDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    tech_nodes: {
      file_path: '';
      selected_values: null;
    };
  };
  total_count: number;
}
interface DidDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    design_ids: {
      file_path: '';
      selected_values: null;
    };
  };
  total_count: number;
}
interface TravelerIdDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    traveler_ids: {
      file_path: '';
      selected_values: null;
    };
  };
  total_count: number;
}
interface TravelerDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    traveler_steps: {
      file_path: '';
      selected_values: null;
    };
    baseline_line_traveler_id: '';
  };
  total_count: number;
}
interface FdContextDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    fd_contexts: {
      file_path: '';
      selected_values: null;
    };
  };
  current_stage_inputs: {
    start_date: String;
    end_date: String;
  };
  total_count: number;
}
interface FdSensorsDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    sensors: {
      file_path: '';
      selected_values: null;
    };
  };
  current_stage_inputs: {
    fd_contexts: {
      file_path: '';
      selected_values: [];
    };
  };
  total_count: number;
}

interface FdTraceDataPullResultResponse {
  current_stage: String;
  current_stage_status: String;
  current_stage_results: {
    fd_trace: {
      file_path: '';
      selected_values: [];
    };
  };
  current_stage_inputs: {
    sensors: {
      file_path: '';
      selected_values: [];
    };
  };
  total_count: number;
}

interface lolIdsDataPullResultResponse {
  start_date: String;
  end_date: String;
  current_stage_inputs: {
    traveler_steps: {
      file_path: '';
      selected_values: [];
    };
    recipes: {
      file_path: '';
      selected_values: [];
    };
    tool_ids: {
      file_path: '';
      selected_values: [];
    };
    step_ids: {
      file_path: '';
      selected_values: [];
    };
    sensors: {
      file_path: '';
      selected_values: [];
    };
  };
  current_stage_status: '';
  current_stage_results: {
    final_data: any;
    lot_ids: {
      file_path: '';
      selected_values: [];
    };
    wafer_ids: {
      file_path: '';
      selected_values: [];
    };
    uc2_sigma_data: {
      file_path: '';
      selected_values: [];
    };
    aggregated_file_path: '';
  };
  traveler_ids: {
    file_path: '';
    selected_values: [];
  };

  facilities: {
    file_path: '';
    selected_values: [];
  };
}

@Injectable({
  providedIn: 'root',
})
export class DataCatalogService {
  runs = new Set<Array<Record<string, any>>>();
  private storageKey = 'selectedSession';

  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  setData(data: any) {
    localStorage.setItem(this.storageKey, JSON.stringify(data));
  }

  getData() {
    const storedData = localStorage.getItem(this.storageKey);
    return storedData ? JSON.parse(storedData) : undefined;
  }

  async getAllSessions(
    project_id: any,
    page_limit: any,
    page_number: any,
  ): Promise<AllSessionsResponse> {
    let projectId = this.configService.SelectedProjectId;
    let url: string = `${environment.tdamUrl}/micron/data_catalog/get_all_sessions?projectId=${project_id}&page_limit=${page_limit}&page_number=${page_number}`;
    let result = await this.http.get(url).toPromise();
    return result as AllSessionsResponse;
  }

  private getAccessToken(): string {
    const currentUser = localStorage.getItem('currentUser');
    return currentUser ? JSON.parse(currentUser).access_token : '';
  }

  createSession(data: any): Observable<any> {
    const token = this.getAccessToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/create_session?token=${token}`;
    return this.http.post(url, data, {
      headers: headers,
      observe: 'response',
    });
  }

  createJob(payload: any, job_id: any, type: String): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/${type}?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  async dataPullStatus(
    job_id: any,
    stage: any = null,
  ): Promise<DataPullStatusResponse> {
    let url;
    if (stage !== null) {
      url = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_status?data_pull_job_id=${job_id}&stage=${stage}`;
    } else
      url = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_status?data_pull_job_id=${job_id}`;
    let result = await this.http.get(url).toPromise();
    return result as DataPullStatusResponse;
  }

  // async fetchToolNamesAndIds(uc2_fd_aggregate_tools_filepath: string, pageDetails: any): Promise<HttpResponse<ToolStatus[]>> {
  //   if (uc2_fd_aggregate_tools_filepath) {
  //     try {
  //       const result2: any = await lastValueFrom(this.getQueryResponse(uc2_fd_aggregate_tools_filepath, {}, [], [], pageDetails));

  //       let res = result2?.body['data'];
  //       console.log('res...', res);

  //       let final_results: ToolStatus[] = [];
  //       for (let i = 0; i < res.length; i++) {
  //         const tool = res[i];
  //         console.log(tool, 'ran');
  //         const new_tool_value: ToolStatus = {
  //           tool_name: tool['tool_name'],
  //           tool_id: tool['tool_id'],
  //         };
  //         final_results.push(new_tool_value);
  //       }

  //       console.log('final_results:', final_results);

  //       return new HttpResponse<ToolStatus[]>({
  //         body: final_results,
  //         status: 200,
  //       });

  //     } catch (error) {
  //       console.error('Error fetching tools:', error);
  //       return new HttpResponse<ToolStatus[]>({
  //         body: [],
  //         status: 500,
  //       });
  //     }
  //   }
  //   return new HttpResponse<ToolStatus[]>({
  //     body: [],
  //     status: 400, // Bad Request, if filepath is not provided
  //   });
  // }

  //   async generateTools(
  //     job_id: any,
  //     config: any
  //   ): Promise<HttpResponse<ToolStatus[]>> {
  //     const headers = new HttpHeaders({
  //       'Content-Type': 'application/json',
  //     });

  //     const url: string = `${environment.tdamUrl}/micron/data_catalog/fd/tool?data_pull_job_id=${job_id}`;

  //     // Define payload based on config
  //     const payload = {
  //       traveler_steps: {
  //         file_path: config.traveler_steps.file_path || 'default_file_path',
  //         selected_values: config.traveler_steps.selected_values || []
  //       },
  //       start_date: config.start_date || '2024-09-10',
  //       end_date: config.end_date || '2024-09-10',
  //       traveler_ids: {
  //         file_path: config.traveler_ids.file_path || 'default_file_path',
  //         selected_values: config.traveler_ids.selected_values || []
  //       },
  //       design_ids: {
  //         file_path: config.design_ids.file_path || 'default_file_path',
  //         selected_values: config.design_ids.selected_values || []
  //       },
  //       facilities: {
  //         file_path: config.facilities.file_path || 'default_file_path',
  //         selected_values: config.facilities.selected_values || []
  //       }
  //     };

  //     console.log(url, payload, "payload values");  // For debugging

  //     try {
  //       const result = await this.http.post<ToolAPIResponse>(url, payload, {
  //         headers,
  //         observe: 'response',
  //       }).toPromise();

  //       if(result){
  //         console.log("result..rk",result)
  //         let pageDetails = {
  //           pageIndex: 0,
  //           pageSize: 100000, //TODO : implement proper pagination here later
  //         };
  //         // Usage:

  //         //missing : fetch only unique tool names...
  //         let uc2_fd_aggregate_tools_filepath = result.body?.tools.file_path;
  //         config.uc2_fd_aggregate_tools_filepath = uc2_fd_aggregate_tools_filepath
  //         console.log('uc2_fd_aggregate_tools_filepath: ',uc2_fd_aggregate_tools_filepath)
  //         if (uc2_fd_aggregate_tools_filepath){
  //           const response = await this.fetchToolNamesAndIds(uc2_fd_aggregate_tools_filepath, pageDetails);
  //           console.log('final final_results:', response.body);
  //           return response

  //           }

  //         }

  //       return new HttpResponse<ToolStatus[]>({
  //         body: [],
  //         status: 200,
  //       });
  //     } catch (error) {
  //       console.error('Error fetching tools:', error);
  //       return new HttpResponse<ToolStatus[]>({
  //         body: [],
  //         status: 500,
  //         statusText: 'Internal Server Error',
  //       });
  //     }
  //   }

  //   async finalaggregateData(
  //     job_id: any,
  //     config: any
  //   ): Promise<HttpResponse<FinalStatus[]>> { console.log(config,"final config");
  //     const headers = new HttpHeaders({
  //       'Content-Type': 'application/json',
  //     });

  //     const url: string = `${environment.tdamUrl}/micron/data_catalog/fd/final_aggregate_data?data_pull_job_id=${job_id}`;

  //     // Define payload based on config
  //     const payload = {
  //       tools: {
  //         file_path: '',
  //         selected_values: config.selected_tools || []
  //       },
  //       step_ids: {
  //         file_path: config.step_ids.file_path || '',
  //         selected_values: config.step_ids.selected_values || []
  //       },
  //       sensors: {
  //         file_path: config.sensors.file_path || '',
  //         selected_values: config.sensors.selected_values || []
  //       },
  //       traveler_steps: {
  //         file_path: config.traveler_steps.file_path || 'default_file_path',
  //         selected_values: config.traveler_steps.selected_values || []
  //       },
  //       start_date: config.start_date || '2024-09-10',
  //       end_date: config.end_date || '2024-09-10',
  //       traveler_ids: {
  //         file_path: config.traveler_ids.file_path || 'default_file_path',
  //         selected_values: config.traveler_ids.selected_values || []
  //       },
  //       design_ids: {
  //         file_path: config.design_ids.file_path || 'default_file_path',
  //         selected_values: config.design_ids.selected_values || []
  //       },
  //       facilities: {
  //         file_path: config.facilities.file_path || 'default_file_path',
  //         selected_values: config.facilities.selected_values || []
  //       }
  //     };

  //     console.log(url, payload, "payload values");  // For debugging

  //     try {
  //       const result = await this.http.post<FinalStatus[]>(url, payload, {
  //         headers,
  //         observe: 'response',
  //       }).toPromise();

  //       return result || new HttpResponse<FinalStatus[]>({
  //         body: [],
  //         status: 200,
  //       });
  //     } catch (error) {
  //       console.error('Error fetching tools:', error);
  //       return new HttpResponse<FinalStatus[]>({
  //         body: [],
  //         status: 500,
  //         statusText: 'Internal Server Error',
  //       });
  //     }
  //   }

  //   async generateStepIds(
  //     job_id: any,
  //     config: any
  //   ): Promise<HttpResponse<StepIdSensorResponse>> {
  //     const headers = new HttpHeaders({
  //       'Content-Type': 'application/json',
  //     });

  //     const url: string = `${environment.tdamUrl}/micron/data_catalog/fd/sensors_and_step_ids?data_pull_job_id=${job_id}`;

  //     // Define payload based on config
  //     const payload = {
  //       tools: {
  //          file_path: config.uc2_fd_aggregate_tools_filepath || 'default_file_path',
  //          selected_values: config.selected_tools || []
  //       },
  //       traveler_steps: {
  //         file_path: config.traveler_steps.file_path || 'default_file_path',
  //         selected_values: config.traveler_steps.selected_values || []
  //       },
  //       start_date: config.start_date || '2024-09-10',
  //       end_date: config.end_date || '2024-09-10',
  //       traveler_ids: {
  //         file_path: config.traveler_ids.file_path || 'default_file_path',
  //         selected_values: config.traveler_ids.selected_values || []
  //       },
  //       design_ids: {
  //         file_path: config.design_ids.file_path || 'default_file_path',
  //         selected_values: config.design_ids.selected_values || []
  //       },
  //       facilities: {
  //         file_path: config.facilities.file_path || 'default_file_path',
  //         selected_values: config.facilities.selected_values || []
  //       }
  //     };

  //     console.log(url, payload, "payload values");  // For debugging

  //     try {
  //       const result = await this.http.post<StepIdSensorResponse>(url, payload, {
  //         headers,
  //         observe: 'response',
  //       }).toPromise();

  //       return result || new HttpResponse<StepIdSensorResponse>({
  //         body: {
  //           sensors: {
  //             file_path: '/hexaind-data/dummy_data/sensors.parquet',
  //             selected_values: []
  //           },
  //           step_ids: {
  //             file_path: '/hexaind-data/dummy_data/step_ids.parquet',
  //             selected_values: []
  //           }
  //         },
  //         status: 200,
  //       });
  //     } catch (error) {
  //       console.error('Error fetching step IDs and sensors:', error);
  //       return new HttpResponse<StepIdSensorResponse>({
  //         body: {
  //           sensors: {
  //             file_path: '/hexaind-data/dummy_data/sensors.parquet',
  //             selected_values: []
  //           },
  //           step_ids: {
  //             file_path: '/hexaind-data/dummy_data/step_ids.parquet',
  //             selected_values: []
  //           }
  //         },
  //         status: 500,
  //         statusText: 'Internal Server Error',
  //       });
  //     }
  //   }

  //   async getStepIds(
  //     path: string
  //   ): Promise<HttpResponse<StepIdResponse>> {
  //     const headers = new HttpHeaders({
  //       'Content-Type': 'application/json',
  //     });

  //     const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

  //     // Define the payload structure
  //     const payload = {
  //       page_number: 1,
  //       page_size: 100,
  //       ignore_pagination: true,
  //       path: path,   // Dynamically pass the 'path' argument
  //       column: 'STEP_ID'  // Dynamically pass the 'column' argument
  //     };

  //     console.log(url, payload, "payload values");  // For debugging

  //     try {
  //       const result = await this.http.post<StepIdResponse>(url, payload, {
  //         headers,
  //         observe: 'response',
  //       }).toPromise();

  //       return result || new HttpResponse<StepIdResponse>({
  //         body: {
  //           uniques: [],
  //           rows_count: 0,
  //         },
  //         status: 200,
  //       });
  //     } catch (error) {
  //       console.error('Error fetching step IDs and sensors:', error);

  //       return new HttpResponse<StepIdResponse>({
  //         body: {
  //           uniques: [],
  //           rows_count: 0,
  //         },
  //         status: 500,
  //         statusText: 'Internal Server Error',
  //       });
  //     }
  //   }

  //   async getSensors(
  //     path: string
  //   ): Promise<HttpResponse<StepIdResponse>> {
  //     const headers = new HttpHeaders({
  //       'Content-Type': 'application/json',
  //     });

  //     const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

  //     // Define the payload structure
  //     const payload = {
  //       page_number: 1,
  //       page_size: 100,
  //       ignore_pagination: true,
  //       path: path,   // Dynamically pass the 'path' argument
  //       column: 'SENSOR'  // Dynamically pass the 'column' argument
  //     };

  //     console.log(url, payload, "payload values");  // For debugging

  //     try {
  //       const result = await this.http.post<StepIdResponse>(url, payload, {
  //         headers,
  //         observe: 'response',
  //       }).toPromise();

  //       return result || new HttpResponse<StepIdResponse>({
  //         body: {
  //           uniques: [],
  //           rows_count: 0,
  //         },
  //         status: 200,
  //       });
  //     } catch (error) {
  //       console.error('Error fetching step IDs and sensors:', error);

  //       return new HttpResponse<StepIdResponse>({
  //         body: {
  //           uniques: [],
  //           rows_count: 0,
  //         },
  //         status: 500,
  //         statusText: 'Internal Server Error',
  //       });
  //     }
  //   }

  async fetchToolNamesAndIds(
    uc2_fd_aggregate_tools_filepath: string,
    pageDetails: any,
  ): Promise<HttpResponse<ToolStatus[]>> {
    if (uc2_fd_aggregate_tools_filepath) {
      try {
        const result2: any = await lastValueFrom(
          this.getQueryResponse(
            uc2_fd_aggregate_tools_filepath,
            {},
            [],
            [],
            pageDetails,
          ),
        );

        let res = result2?.body['data'];

        let final_results: ToolStatus[] = [];
        for (let i = 0; i < res.length; i++) {
          const tool = res[i];
          console.log(tool, 'ran');
          const new_tool_value: ToolStatus = {
            tool_name: tool['tool_name'],
            tool_id: tool['tool_id'],
            data: [],
          };
          final_results.push(new_tool_value);
        }

        return new HttpResponse<ToolStatus[]>({
          body: final_results,
          status: 200,
        });
      } catch (error) {
        console.error('Error fetching tools:', error);
        return new HttpResponse<ToolStatus[]>({
          body: [],
          status: 500,
        });
      }
    }
    return new HttpResponse<ToolStatus[]>({
      body: [],
      status: 400, // Bad Request, if filepath is not provided
    });
  }

  async fetchRecipesNamesAndIds(
    uc2_fd_aggregate_recipes_filepath: string,
  ): Promise<HttpResponse<RecipeAPIResponse[]>> {
    if (uc2_fd_aggregate_recipes_filepath) {
      console.log(uc2_fd_aggregate_recipes_filepath, 'file path recipes');

      const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

      const payload = {
        ignore_pagination: true,
        path: uc2_fd_aggregate_recipes_filepath,
        column: 'RECIPE',
      };

      try {
        const result = await this.http
          .post<FetchRecipesResponse>(url, payload, {
            observe: 'response',
          })
          .toPromise();

        if (result && result.body) {
          // Check if `result.body.uniques` is defined and not null
          const uniques = result.body.uniques || [];

          // Map the response to RecipeAPIResponse format
          const recipeApiResponses: RecipeAPIResponse[] = uniques.map(
            (uniqueName, index) => ({
              recipe_name: uniqueName,
            }),
          );

          return new HttpResponse<RecipeAPIResponse[]>({
            body: recipeApiResponses,
            status: 200,
          });
        } else {
          // Handle the case where result or result.body is null or undefined
          return new HttpResponse<RecipeAPIResponse[]>({
            body: [],
            status: 204, // No Content
          });
        }
      } catch (error) {
        console.error('Error fetching recipes:', error);
        return new HttpResponse<RecipeAPIResponse[]>({
          body: [],
          status: 500,
          statusText: 'Internal Server Error',
        });
      }
    }

    return new HttpResponse<RecipeAPIResponse[]>({
      body: [],
      status: 400, // Bad Request if filepath is not provided
    });
  }

  async generateRecipes(
    job_id: any,
    config: any,
    path: any,
  ): Promise<HttpResponse<RecipeAPIResponse[]>> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/fd/generate_final_data_aggregate_context?data_pull_job_id=${job_id}`;

    const payload = {
      traveler_steps: {
        file_path: config.traveler_steps.file_path || 'default_file_path',
        selected_values: config.traveler_steps.selected_values || [],
      },
      start_date: config.start_date || '2024-09-10',
      end_date: config.end_date || '2024-09-10',
      traveler_ids: {
        file_path: config.traveler_ids.file_path || 'default_file_path',
        selected_values: config.traveler_ids.selected_values || [],
      },
      design_ids: {
        file_path: config.design_ids.file_path || 'default_file_path',
        selected_values: config.design_ids.selected_values || [],
      },
      facilities: {
        file_path: config.facilities.file_path || 'default_file_path',
        selected_values: config.facilities.selected_values || [],
      },
    };

    try {
      let result;
      if (path == '') {
        result = await this.http
          .post<GenerateRecipesResponse>(url, payload, {
            headers,
            observe: 'response',
          })
          .toPromise();
      } else {
        result = {
          body: {
            recipes: {
              file_path: path,
              selected_values: [],
            },
            tool_ids: {
              file_path: path,
              selected_values: [],
            },
            step_ids: {
              file_path: path,
              selected_values: [],
            },
            sensors: {
              file_path: path,
              selected_values: [],
            },
          },
        };
      }

      if (result) {
        const uc2_fd_aggregate_recipe_filepath =
          result.body?.recipes?.file_path;

        if (uc2_fd_aggregate_recipe_filepath) {
          const response = await this.fetchRecipesNamesAndIds(
            uc2_fd_aggregate_recipe_filepath,
          );
          return response;
        } else {
          // Handle the case where file_path is not available
          return new HttpResponse<RecipeAPIResponse[]>({
            body: [],
            status: 204, // No Content
          });
        }
      }

      return new HttpResponse<RecipeAPIResponse[]>({
        body: [],
        status: 204, // No Content
      });
    } catch (error) {
      console.error('Error fetching Recipes:', error);
      return new HttpResponse<RecipeAPIResponse[]>({
        body: [],
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async onGeneratePathClick(
    job_id: any,
    config: any,
  ): Promise<HttpResponse<GenerateRecipesResponse>> {
    // Changed here
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/fd/generate_final_data_aggregate_context?data_pull_job_id=${job_id}`;

    const payload = {
      traveler_steps: {
        file_path: config.traveler_steps.file_path || 'default_file_path',
        selected_values: config.traveler_steps.selected_values || [],
      },
      start_date: config.start_date || '2024-09-10',
      end_date: config.end_date || '2024-09-10',
      traveler_ids: {
        file_path: config.traveler_ids.file_path || 'default_file_path',
        selected_values: config.traveler_ids.selected_values || [],
      },
      design_ids: {
        file_path: config.design_ids.file_path || 'default_file_path',
        selected_values: config.design_ids.selected_values || [],
      },
      facilities: {
        file_path: config.facilities.file_path || 'default_file_path',
        selected_values: config.facilities.selected_values || [],
      },
    };

    try {
      const result = await this.http
        .post<GenerateRecipesResponse>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      if (result && result.body) {
        return result; // Return single object
      }

      return new HttpResponse<GenerateRecipesResponse>({
        body: {} as GenerateRecipesResponse, // Return an empty object if no content
        status: 204, // No Content
      });
    } catch (error) {
      console.error('Error fetching Recipes:', error);
      return new HttpResponse<GenerateRecipesResponse>({
        body: {} as GenerateRecipesResponse,
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async finalaggregateData(
    job_id: any,
    config: any,
  ): Promise<HttpResponse<FinalStatus[]>> {
    console.log(config, 'final config');
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/fd/final_data_aggregate?data_pull_job_id=${job_id}`;

    function flattenArray(array: any[]): any[] {
      return array.reduce(
        (acc, val) => acc.concat(Array.isArray(val) ? flattenArray(val) : val),
        [],
      );
    }

    // Define payload based on config
    const payload = {
      recipes: {
        file_path: config.recipes.file_path,
        selected_values: config.selectedRecipeNames || [],
      },
      tool_ids: {
        file_path: config.tool_ids.file_path,
        selected_values: config.tool_ids.selected_values || [],
      },
      step_ids: {
        file_path: config.step_ids.file_path || '',
        selected_values: config.step_ids.selected_values || [],
      },
      sensors: {
        file_path: config.sensors.file_path || '',
        selected_values: config.sensors.selected_values || [],
      },
      traveler_steps: {
        file_path: config.traveler_steps.file_path || 'default_file_path',
        selected_values: config.traveler_steps.selected_values || [],
      },
      start_date: config.start_date || '2024-09-10',
      end_date: config.end_date || '2024-09-10',
      traveler_ids: {
        file_path: config.traveler_ids.file_path || 'default_file_path',
        selected_values: config.traveler_ids.selected_values || [],
      },
      design_ids: {
        file_path: config.design_ids.file_path || 'default_file_path',
        selected_values: config.design_ids.selected_values || [],
      },
      facilities: {
        file_path: config.facilities.file_path || 'default_file_path',
        selected_values: config.facilities.selected_values || [],
      },
    };

    try {
      const result = await this.http
        .post<FinalStatus[]>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      return (
        result ||
        new HttpResponse<FinalStatus[]>({
          body: [],
          status: 200,
        })
      );
    } catch (error) {
      console.error('Error fetching tools:', error);
      return new HttpResponse<FinalStatus[]>({
        body: [],
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async generateToolIds(
    file_path: any,
    selected_values: any,
  ): Promise<HttpResponse<ToolStatus>> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/data`;

    function flattenArray(array: any[]): any[] {
      return array.reduce(
        (acc, val) => acc.concat(Array.isArray(val) ? flattenArray(val) : val),
        [],
      );
    }
    //[[dsf,adsf],[dafa,adfa,]]
    // Example payload construction
    const payload = {
      path: file_path,
      filters: {
        RECIPE: {
          operation: 'EQ',
          value: selected_values, // Flattened array
        },
      },
      included_columns: ['TOOL_ID', 'TOOL_NAME'],
      is_unique: true,
    };

    try {
      const result = await this.http
        .post<ToolStatus>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      return (
        result ||
        new HttpResponse<ToolStatus>({
          status: 200,
        })
      );
    } catch (error) {
      console.error('Error fetching step IDs and sensors:', error);
      return new HttpResponse<ToolStatus>({
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async generateStepIds(
    file_path: any,
    selectedRecipeNames: any,
    selectedToolIds: any,
  ): Promise<HttpResponse<StepIdResponse>> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

    function flattenArray(array: any[]): any[] {
      return array.reduce(
        (acc, val) => acc.concat(Array.isArray(val) ? flattenArray(val) : val),
        [],
      );
    }

    const payload = {
      path: file_path,
      filters: {
        RECIPE: {
          operation: 'EQ',
          value: selectedRecipeNames, // Flattened array
        },
        TOOL_ID: {
          operation: 'EQ',
          value: selectedToolIds,
        },
      },
      ignore_pagination: true,
      column: 'STEP_ID',
    };

    try {
      const result = await this.http
        .post<StepIdResponse>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      return (
        result ||
        new HttpResponse<StepIdResponse>({
          status: 200,
        })
      );
    } catch (error) {
      console.error('Error fetching step IDs and sensors:', error);
      return new HttpResponse<StepIdResponse>({
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async generateSensors(
    file_path: any,
    selectedRecipeNames: any,
    selectedToolIds: any,
    selected_step_ids: any,
  ): Promise<HttpResponse<StepIdResponse>> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

    function flattenArray(array: any[]): any[] {
      return array.reduce(
        (acc, val) => acc.concat(Array.isArray(val) ? flattenArray(val) : val),
        [],
      );
    }

    // Example payload construction
    const payload = {
      path: file_path,
      filters: {
        RECIPE: {
          operation: 'EQ',
          value: selectedRecipeNames, //flattenArray(config.selectedRecipeNames),
        },
        TOOL_ID: {
          operation: 'EQ',
          value: selectedToolIds, //flattenArray(config.selectedToolIds),
        },
        STEP_ID: {
          operation: 'EQ',
          value: selected_step_ids, //flattenArray(config.step_ids.selected_values),
        },
      },
      ignore_pagination: true,
      column: 'SENSOR',
    };

    try {
      const result = await this.http
        .post<StepIdResponse>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      return (
        result ||
        new HttpResponse<StepIdResponse>({
          status: 200,
        })
      );
    } catch (error) {
      console.error('Error fetching step IDs and sensors:', error);
      return new HttpResponse<StepIdResponse>({
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async getStepIds(path: string): Promise<HttpResponse<StepIdResponse>> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

    // Define the payload structure
    const payload = {
      page_number: 1,
      page_size: 100,
      ignore_pagination: true,
      path: path, // Dynamically pass the 'path' argument
      column: 'STEP_ID', // Dynamically pass the 'column' argument
    };

    try {
      const result = await this.http
        .post<StepIdResponse>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      return (
        result ||
        new HttpResponse<StepIdResponse>({
          body: {
            uniques: [],
            rows_count: 0,
          },
          status: 200,
        })
      );
    } catch (error) {
      console.error('Error fetching step IDs and sensors:', error);

      return new HttpResponse<StepIdResponse>({
        body: {
          uniques: [],
          rows_count: 0,
        },
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async getSensors(path: string): Promise<HttpResponse<StepIdResponse>> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;

    // Define the payload structure
    const payload = {
      page_number: 1,
      page_size: 100,
      ignore_pagination: true,
      path: path, // Dynamically pass the 'path' argument
      column: 'SENSOR', // Dynamically pass the 'column' argument
    };

    try {
      const result = await this.http
        .post<StepIdResponse>(url, payload, {
          headers,
          observe: 'response',
        })
        .toPromise();

      return (
        result ||
        new HttpResponse<StepIdResponse>({
          body: {
            uniques: [],
            rows_count: 0,
          },
          status: 200,
        })
      );
    } catch (error) {
      console.error('Error fetching step IDs and sensors:', error);

      return new HttpResponse<StepIdResponse>({
        body: {
          uniques: [],
          rows_count: 0,
        },
        status: 500,
        statusText: 'Internal Server Error',
      });
    }
  }

  async fabPullResult(
    job_id: any,
    stage: string,
  ): Promise<FabDataPullResultResponse> {
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as FabDataPullResultResponse;
  }

  async techPullResult(
    payload: any,
    job_id: any,
    stage: String,
  ): Promise<TechDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as TechDataPullResultResponse;
  }
  async didPullResult(
    payload: any,
    job_id: any,
    stage: string,
  ): Promise<DidDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as DidDataPullResultResponse;
  }
  async travelerIdPullResult(
    payload: any,
    job_id: any,
    stage: string,
  ): Promise<TravelerIdDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as TravelerIdDataPullResultResponse;
  }
  async travelerPullResult(
    payload: any,
    job_id: any,
    stage: string,
  ): Promise<TravelerDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as TravelerDataPullResultResponse;
  }
  async downloadDataResult(
    payload: any,
    job_id: any,
    stage: string,
  ): Promise<FdContextDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as FdContextDataPullResultResponse;
  }

  async sensorsPullResult(
    payload: any,
    job_id: any,
    stage: string,
  ): Promise<FdSensorsDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as FdSensorsDataPullResultResponse;
  }
  async fdTracePullResult(
    payload: any,
    job_id: any,
    stage: string,
  ): Promise<FdTraceDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as FdTraceDataPullResultResponse;
  }

  getQueryResponse(
    path: String,
    filteredData: any,
    included_columns: [],
    excluded_columns: [],
    pageDetails: any,
  ): Observable<any> {
    let payload = {
      path: path,
      included_columns: included_columns,
      excluded_columns: excluded_columns,
      filters: filteredData,
      page_number: pageDetails.pageIndex + 1,
      page_size: pageDetails.pageSize,
    };
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/query/data`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }
  // getQueryUniques(
  //   path: String,
  //   column: String,
  //   pageDetails: any,
  //   filter: any = {}
  // ): Observable<any> {

  //   let transformedFilters: [string, { operation: string; value: string; }, string][] = [];

  //   if (Array.isArray(filter)) {
  //     transformedFilters = filter.map((filterItem: { function: string; value: string | string[]; operator: string }, index: number) => {

  //       const column = index === 0 ? "run_parameters" : `run_parameters`;

  //       return [
  //         column,
  //         {
  //           operation: filterItem.function,
  //           value: typeof filterItem.value === 'string' ? filterItem.value : filterItem.value.join(', '),
  //         },
  //         filterItem.operator
  //       ];
  //     });
  //   }

  //   let page_size = 100000;
  //   if (column == "run_parameters" || column == "COMMON_TEST_ID" || column == "point_parameters") {
  //     page_size = 1000;
  //   }

  //   let payload = {
  //     path: path,
  //     column: column,
  //     filters: transformedFilters,
  //     page_number: pageDetails.pageIndex + 1,
  //     page_size: page_size,
  //   };

  //   const headers = new HttpHeaders({
  //     'Content-Type': 'application/json',
  //   });

  //   let url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;
  //   return this.http.post(url, payload, {
  //     headers: headers,
  //     observe: 'response',
  //   });
  // }

  getQueryUniques(
    path: String,
    column: String,
    pageDetails: any,
    filter: any = {},
    searchString?: any, // Making searchString optional
    isItATotalDataFetch?: any,
  ): Observable<any> {
    let transformedFilters: [
      string,
      { operation: string; value: string },
      string,
    ][] = [];

    // Apply search filter only if filter is 'search' and searchString is provided
    if (filter === 'search' && searchString) {
      transformedFilters = [
        [
          'run_parameters',
          {
            operation: 'LQ',
            value: searchString,
          },
          'AND',
        ],
      ];
      console.log(transformedFilters, 'transformed filters for search');
    } else if (Array.isArray(filter)) {
      // Process only if filter is an array
      transformedFilters = filter.map(
        (
          filterItem: {
            function: string;
            value: string | string[];
            operator: string;
          },
          index: number,
        ) => {
          const column = index === 0 ? 'run_parameters' : `run_parameters`;

          return [
            column,
            {
              operation: filterItem.function,
              value:
                typeof filterItem.value === 'string'
                  ? filterItem.value
                  : filterItem.value.join(', '),
            },
            filterItem.operator,
          ];
        },
      );
      console.log(
        transformedFilters,
        'transformed filters for regular filters',
      );
    }

    let page_size = 100000;
    if (
      column === 'run_parameters' ||
      column === 'COMMON_TEST_ID' ||
      column === 'point_parameters'
    ) {
      page_size = 1000;
    }

    let payload = {
      path: path,
      column: column,
      filters: transformedFilters,
      page_number: pageDetails.pageIndex + 1,
      page_size: page_size,
      ignore_pagination: false,
    };

    if (isItATotalDataFetch) payload.ignore_pagination = true;

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    let url: string = `${environment.tdamUrl}/micron/data_catalog/query/uniques`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  getQueryUniquesAdvanced(
    path: String,
    column: String,
    pageDetails: any,
    selected_path: string,
    filter: any = {},
    searchString?: any,
  ): Observable<any> {
    let transformedFilters: [
      string,
      { operation: string; value: string },
      string,
    ][] = [];

    // Apply search filter only if filter is 'search' and searchString is provided
    if (filter === 'search' && searchString) {
      transformedFilters = [
        [
          'run_parameters',
          {
            operation: 'LQ',
            value: searchString,
          },
          'AND',
        ],
      ];
    } else if (Array.isArray(filter)) {
      // Process only if filter is an array
      transformedFilters = filter.map(
        (
          filterItem: {
            function: string;
            value: string | string[];
            operator: string;
          },
          index: number,
        ) => {
          const column = index === 0 ? 'run_parameters' : `run_parameters`;

          return [
            column,
            {
              operation: filterItem.function,
              value:
                typeof filterItem.value === 'string'
                  ? filterItem.value
                  : filterItem.value.join(', '),
            },
            filterItem.operator,
          ];
        },
      );
    }

    let page_size = 100000;
    if (
      column === 'run_parameters' ||
      column === 'COMMON_TEST_ID' ||
      column === 'point_parameters'
    ) {
      page_size = 1000;
    }

    let payload = {
      path: path,
      column: column,
      filters: transformedFilters,
      page_number: pageDetails.pageIndex + 1,
      page_size: page_size,
      selected_path: selected_path,
    };

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    let url: string = `${environment.tdamUrl}/micron/data_catalog/query/advanced_uniques `;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  getSelectQueryUniques(
    path: string,
    column: string,
    pageDetails: any,
    filter: any = {},
    operation: string,
    selected_path: any,
    searchTerm?: string,
    selectedValues?: any,
  ): Observable<any> {
    // Default page size; reduced for certain columns
    let page_size = 100000;
    if (
      ['run_parameters', 'COMMON_TEST_ID', 'point_parameters'].includes(column)
    ) {
      page_size = 1000;
    }

    // Base payload structure
    let payload: any = {
      path: path,
      column: column,
      filters: filter,
      page_number: pageDetails.pageIndex + 1,
      page_size: page_size,
      selection: {
        operation: operation,
      },
      selected_path: selected_path,
    };

    // Conditionally add fields to `selection` based on `operation`
    if (operation === 'QUERY') {
      if (searchTerm) {
        payload.selection.query = searchTerm; // Add query if searchTerm is provided
      } else {
        payload.selection.query = '';
        console.log('Search term is empty; adjust filtering as needed.');
        // Optionally modify the payload or handle as per your logic
      }
    } else if (operation === 'MANUAL' && selectedValues) {
      payload.selection.values = selectedValues; // Use selected values if available
    }

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/select`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  getUnSelectQueryUniques(
    path: string,
    column: string,
    pageDetails: any,
    filter: any = {},
    operation: string,
    selected_path: any,
    searchTerm?: string,
    selectedValues?: any,
  ): Observable<any> {
    // Default page size; reduced for certain columns
    let page_size = 100000;
    if (
      ['run_parameters', 'COMMON_TEST_ID', 'point_parameters'].includes(column)
    ) {
      page_size = 1000;
    }

    // Base payload structure
    let payload: any = {
      path: path,
      column: column,
      filters: filter,
      page_number: pageDetails.pageIndex + 1,
      page_size: page_size,
      selection: {
        operation: operation,
      },
      selected_path: selected_path,
    };

    // Conditionally add fields to `selection` based on `operation`
    if (operation === 'QUERY') {
      if (searchTerm) {
        payload.selection.query = searchTerm; // Add query if searchTerm is provided
      } else {
        payload.selection.query = 'hello';
        // Optionally modify the payload or handle as per your logic
      }
    } else if (operation === 'MANUAL' && selectedValues) {
      payload.selection.values = selectedValues; // Use selected values if available
    }

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const url: string = `${environment.tdamUrl}/micron/data_catalog/query/unselect`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  async cancelPolling(job_id: any): Promise<String> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_trace_pull_stop?data_pull_job_id=${job_id}`;
    let result = await this.http.get(url).toPromise();
    return result as String;
  }

  async travelerStepsResponse(path: any): Promise<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let encodedUrl = encodeURIComponent(path);
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/traveler_steps?path=${encodedUrl}`;
    let result = await this.http.get(url).toPromise();
    return result as any;
  }

  lotIdsResponse(job_id: any, payload: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/lot_ids?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  async getLotsIdsStatus(
    job_id: any,
    stage: any,
  ): Promise<lolIdsDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as lolIdsDataPullResultResponse;
  }

  waferIdsResponse(job_id: any, payload: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/wafer_ids?data_pull_job_id=${job_id}`;
    console.log(url, payload);
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  async getWaferIdsStatus(
    job_id: any,
    stage: any,
  ): Promise<lolIdsDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = await this.http.get(url).toPromise();
    return result as lolIdsDataPullResultResponse;
  }

  FDContextResponse(job_id: any, payload: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_context?data_pull_job_id=${job_id}`;
    console.log(url, payload);
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  getFDContextQueryResponse(
    path: string,
    save: boolean,
    do_not_send_data: boolean,
    ignore_pagination: boolean,
    filteredData: any,
    pageDetails: any,
  ): Observable<any> {
    let payload = {
      path: path,
      save: save,
      do_not_send_data: do_not_send_data,
      ignore_pagination: ignore_pagination,
      filters: filteredData,
      page_number: pageDetails.pageIndex + 1,
      page_size: pageDetails.pageSize,
    };
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/query/data`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  fdContextFilterApplyResponse(
    job_id: any,
    config: any,
    filteredData: any,
    fdContextFilterApplyPath: string,
    pageDetails: any,
  ): Observable<any> {
    let payload_ = {
      path: fdContextFilterApplyPath,
      filters: filteredData,
    };
    let payload = { ...config, ...payload_ };
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc3_fd_context_apply_filters?data_pull_job_id=${job_id}`;
    console.log(url, payload);
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  async getFDContextApplyFilterStatus(job_id: any, stage: any): Promise<any> {
    //lolIdsDataPullResultResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${
      environment.tdamUrl
    }/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage.toUpperCase()}&ignore_last_run_level=true`;
    let result = await this.http.get(url).toPromise();
    return result; // as lolIdsDataPullResultResponse;
  }

  fdContextPullResult(
    jobId: any,
    filteredData: any,
    config: any,
    fdContextFilterApplyPath: string,
    pageDetails: any,
  ): Observable<any> {
    let payload = {
      path: fdContextFilterApplyPath,
      data_pull_job_id: jobId,
      filters: filteredData,
      page_number: pageDetails.pageIndex + 1,
      page_size: pageDetails.pageSize,
    };
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc3_fd_context_apply_filters`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  saveHighLevelDc(payload: any, job_id: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/save_hl_dc_inputs?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  saveHighLevelResponseResult(job_id: any, stage: string): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}&ignore_last_run_level=true`;
    let result = this.http.get(url);
    return result;
  }
  getGQLFileData(selectedFile: FormData): Observable<any> {
    let file: File;

    console.log('API selectedFile : ', selectedFile);
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/convert_gql_file_to_parquet`;
    return this.http.post<any>(url, selectedFile);
  }

  sigmaGenerateData(job_id: any, config: any) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let payload = {
      data_pull_job_id: job_id,
      config: config,
    };
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc2_sigma_dropdowns_files?data_pull_job_id=${job_id}`;
    return this.http.post(url, config, {
      headers: headers,
      observe: 'response',
    });
    ///micron/data_catalog/fd/uc2_sigma_stage_job
  }

  sigmaDownloadData(job_id: any, config: any, uc2SelectedData: any) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    // let payload_ = {
    //   uc2SelectedData: uc2SelectedData,
    //   config: config,
    // };
    let payload = { ...config, ...uc2SelectedData };
    console.log('the payload is : ', payload);
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc2_sigma_stage_job?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  onUC2SigmaMeasurementSteps(job_id: any, config: any, uc2SelectedData: any) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let payload = { ...config, ...uc2SelectedData };
    console.log('the payload is : ', payload);
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc2_sigma_fetch_based_on_measurement_steps?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  onUC2SigmaPointParameters(job_id: any, config: any, uc2SelectedData: any) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let payload = { ...config, ...uc2SelectedData };
    console.log('the payload is : ', payload);
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc2_sigma_fetch_based_on_point_steps?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  getUC2SigmaTabularFiles(file_path: any) {
    let params = { file_path };
    let url: string = `${environment.tdamUrl}/micron/data_catalog/query/get_tabular_files`;
    return lastValueFrom(this.http.get(url, { params }));
  }

  getUC2SigmaDataPreview(file_path: any) {
    let project_id: any = this.configService.SelectedProjectId;
    const params = { file_path, project_id };
    let url: string = `${environment.tdamUrl}/micron/data_catalog/query/data_preview`;
    return lastValueFrom(this.http.get(url, { params }));
  }

  addToDataset(payload: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let projectId = this.configService.SelectedProjectId;
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/add_to_dataset/${projectId}?name=${payload.name}&description=${payload.description}&file=${payload.file}`;
    return this.http.post(
      url,
      {},
      {
        headers: headers,
        observe: 'response',
      },
    );
  }

  saveMetroSteps(payload: any, job_id: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let projectId = this.configService.SelectedProjectId;
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc3_sigma_fetch_based_on_measurement_steps?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }
  uc3DownloadPath(payload: any, job_id: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let projectId = this.configService.SelectedProjectId;
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc3_sigma_stage_job?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  getUC3ProbeCSVFileData(selectedFile: FormData): Observable<any> {
    let file: File;

    console.log('API selectedFile : ', selectedFile);
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/upload_csv_file_convert_to_parquet`;
    return this.http.post<any>(url, selectedFile);
  }

  ProbeDownloadData(job_id: any, config: any) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    // let payload_ = {
    //   uc2SelectedData: uc2SelectedData,
    //   config: config,
    // };
    // let payload = { ...config, ...uc2SelectedData };
    let payload = config;
    console.log('the payload is : ', payload);
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/probe_data_pull?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  async UC3ProbedataPullStatus(job_id: any, config: any): Promise<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let payload = config;
    let url = `${environment.tdamUrl}/micron/data_catalog/fd/probe_context?data_pull_job_id=${job_id}`;
    const result = await this.http
      .post<FinalStatus[]>(url, payload, {
        headers,
        observe: 'response',
      })
      .toPromise();
  }

  deleteSession(session_id: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    let url = `${environment.tdamUrl}/micron/data_catalog/sessions/${session_id}`;
    return this.http.delete(url, {
      headers,
      observe: 'response',
    });
  }

  saveLotWaferIds(payload: any, job_id: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/save_lot_wafer_inputs?data_pull_job_id=${job_id}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }

  saveLotWaferIdsResponseResult(job_id: any, stage: string): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id=${job_id}&stage=${stage}`;
    let result = this.http.get(url);
    return result;
  }

  async getUC3SimgaMetroStepsPrefixWithNames(
    job_id: any,
    reset: boolean,
  ): Promise<any> {
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/uc3_sigma_get_metro_step_prefixes?data_pull_job_id=${job_id}&reset=${reset}`;
    let result = await this.http.post(url, {}).toPromise();
    return result;
  }

  saveDataSource(payload: any, job_id: any, stage: string): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    let url: string = `${environment.tdamUrl}/micron/data_catalog/fd/save_stage?data_pull_job_id=${job_id}&stage=${stage}`;
    return this.http.post(url, payload, {
      headers: headers,
      observe: 'response',
    });
  }
}
