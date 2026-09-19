import { Component, OnInit } from '@angular/core';
import {
  HttpClient,
  HttpEventType,
} from '@angular/common/http';
import { DateAdapter, MAT_DATE_LOCALE } from '@angular/material/core';
import { DataSheetGenerateService } from '../data-sheet-generate.service';
import { Subscription } from 'rxjs';
import * as Plotly from 'plotly.js-dist-min';
import { ToastrService } from 'ngx-toastr';
import { MatTableDataSource } from '@angular/material/table';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { CustomDateAdapter } from '../custom-date-adapter/custom-date-adapter';
import { NotificationService } from '../notification.service';

@Component({
  selector: 'app-converter',
  templateUrl: './converter.component.html',
  styleUrls: ['./converter.component.less'],
  providers: [
    { provide: DateAdapter, useClass: CustomDateAdapter },
    { provide: MAT_DATE_LOCALE, useValue: 'en-GB' },
  ],
})
export class ConverterComponent implements OnInit {
  uploadProgress: number = 0;

  rawFile: File | null = null;
  rawFileName: string = '';
  rawUploadProgress: number = 0;
  rawUploadSubscription: Subscription | null = null;
  rawFileSize: number = 0;

  fitFile: File | null = null;
  fitFileName: string = '';
  fitUploadProgress: number = 0;
  fitUploadSubscription: Subscription | null = null;
  fitFileSize: number = 0;

  tensileFile: File | null = null;
  tensileRawFileName: string = '';
  tensileRawUploadProgress: number = 0;
  tensileRawUploadSubscription: Subscription | null = null;
  tensileRawFileSize: number = 0;

  uploadedFiles: any = [];
  selectedFile: string | null = null;
  fileSize: string = '';

  flcParameters: any;
  flcResults: boolean = true;

  deleteExistingSubFolder: boolean = true;
  tensileDeleteExisting: boolean = true;
  tensileColumnValues: string[] = [];
  displayedColumns: string[] = [];
  dataSource: any;

  selectedDatetimeColumn: any;
  selectedDirectionColumn: any;
  selectedLengthColumn: any;
  selectedThicknessColumn: any;
  selectedWidthColumn: any;
  tensileResults: any;

  dataSheet!: number;
  nominalAge!: number;
  labReference: string = '';
  operator: string = '';
  preTreatement: string = '';
  timeZone: string = '';

  tensileSavefilePath: boolean = false;
  flcSavefilePath: boolean = false;
  saveTensileLoader: boolean = false;
  saveFLCLoader: boolean = false;
  timeZones = [
    'Asia/Kabul',
    'America/Anchorage',
    'America/Argentina/Buenos_Aires',
    'Australia/Sydney',
    'Europe/Paris',
    'Asia/Tokyo',
    'Africa/Cairo',
    'Pacific/Honolulu',
    'America/Los_Angeles',
    'Asia/Dubai',
    'Europe/London',
    'America/New_York',
    'Asia/Kolkata',
    'America/Mexico_City',
    'Asia/Shanghai',
    'Europe/Moscow',
    'America/Sao_Paulo',
    'Asia/Singapore',
    'Europe/Rome',
    'Pacific/Auckland',
  ];
  uploadFormData: FormData = new FormData();
  dataSheetsNumbers: any;
  dataSheetNumber: string = '';
  showUploadButton: boolean = false;
  totalFileSize: number = 0;
  projectId: string = '';
  graphLoader: boolean = false;

  constructor(
    private http: HttpClient,
    private dataSheetGenerateService: DataSheetGenerateService,
    public toaster: ToastrService,
    private configService: ConfigService,
    private router: Router,
    private notificationService: NotificationService
  ) {
    const selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    selectedProjectId ? (this.projectId = selectedProjectId) : null;
  }

  showMainHeader: boolean = false;
  toggleHeaderButton: string = 'expand_more';
  selectedTab: number = 1;

  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

  showTab(tabNumber: number) {
    this.selectedTab = tabNumber;
    setTimeout(() => {
      if (
        tabNumber == 2 &&
        this.flcParameters &&
        document.getElementById('flcPlotDiv')
      ) {
        this.showFlcPlot(
          this.flcParameters.plot_data.s_raw,
          this.flcParameters.plot_data.df_fit,
          this.flcParameters.plot_data.raw_points,
        );
      }
    }, 0);
  }

  ngOnInit(): void {
    this.getDataSheetSource();
  }

  getDataSheetSource() {
    let obj = {
      base_path: 'base',
    };
    this.dataSheetGenerateService.getDataSheetNumber(obj, this.projectId).subscribe({
      next: (data: any) => {
        this.dataSheetsNumbers = data.datasheets.map((data: any) => data.datasheet);
      },
      error: (error) => {
        console.error(error);
      },
    });
  }

  onDragOver(event: any) {
    event.preventDefault();
  }

  onFileDropped(event: any, fileType: string) {
    event.preventDefault();
    let files = event.dataTransfer.files;
    if (files.length > 0) {
      this.onFileSelected({ target: { files: files } }, fileType);
    }
  }

  onFileSelected(event: any, fileType: string) {
    if (this.selectedTab === 1) {
      const file = event.target.files[0];
      if (file) {
        this.tensileFile = file;
        this.tensileRawFileName = file.name;
        this.tensileRawFileSize = file.size;
        this.uploadTensileFileToConvert();
      }
    }
    if (this.selectedTab === 2) {
      const file = event.target.files[0];
      if (file) {
        const fileAlreadyAdded = this.uploadedFiles.some(
          (uploadedFile: any) => uploadedFile.value === file.name,
        );
        if (!fileAlreadyAdded) {
          this.uploadedFiles.push({ value: file.name, display: file.name });
        }
      }

      if (file) {
        switch (fileType) {
          case 'rawFile':
            this.rawFile = file;
            this.rawFileName = file.name;
            this.rawFileSize = file.size;
            this.uploadFile(file, fileType);
            break;
          case 'fitFile':
            this.fitFile = file;
            this.fitFileName = file.name;
            this.fitFileSize = file.size;
            this.uploadFile(file, fileType);
            break;
        }
      }

      if (this.rawFile && this.fitFile) {
        this.flcResults = true;
      }
    }

    this.resetInput(event);
  }

  resetInput(event: any) {
    event.target.value = '';
  }

  uploadFile(file: File, fileType: 'rawFile' | 'fitFile') {
    this.unsubscribePreviousUpload(fileType);
    const updateProgress = (progress: number) => {
      this.setUploadProgress(progress, fileType);
    };
    let loaded = 0;
    const total = file.size;
    const increment = total / 100;

    const startUploading = () => {
      if (loaded < total) {
        loaded += increment;
        updateProgress(Math.min(100, Math.round((100 * loaded) / total)));
        setTimeout(startUploading, 10);
      } else {
        updateProgress(100);
      }
    };

    startUploading();
  }

  unsubscribePreviousUpload(fileType: 'rawFile' | 'fitFile') {
    const subscription =
      fileType === 'rawFile'
        ? this.rawUploadSubscription
        : this.fitUploadSubscription;
    subscription?.unsubscribe();
  }

  setUploadProgress(progress: number, fileType: 'rawFile' | 'fitFile') {
    if (fileType === 'rawFile') {
      this.rawUploadProgress = progress;
    } else {
      this.fitUploadProgress = progress;
    }
  }

  cancelUpload(fileType: 'rawFile' | 'fitFile') {
    const subscription =
      fileType === 'rawFile'
        ? this.rawUploadSubscription
        : this.fitUploadSubscription;
    subscription?.unsubscribe();
    this.flcResults = false;

    if (fileType === 'rawFile') {
      this.rawUploadProgress = 0;
      this.rawFileName = '';
      this.flcParameters = null;
    } else {
      this.fitUploadProgress = 0;
      this.fitFileName = '';
      this.flcParameters = null;
    }
  }

  uploadTensileFileToConvert(): void {
    this.tensileRawUploadProgress = 0;
    const formData = new FormData();
    if (this.tensileFile) {
      formData.append('tensileFile', this.tensileFile, this.tensileFile.name);
    }
    this.dataSheetGenerateService
      .uploadTensileFileToConvert(this.projectId, formData)
      .subscribe({
        next: (event: any) => {
          if (event.type === HttpEventType.UploadProgress) {
            this.tensileRawUploadProgress = event.total
              ? Math.round((100 * event.loaded) / event.total)
              : this.tensileRawUploadProgress;
          } else if (event.type === HttpEventType.Response) {
            this.toaster.success('File Uploaded Successfully', '', {
              positionClass: 'custom-toast-position',
            });
            this.handleResponse(event.body);
          }
        },
        error: (error) => {
          console.error('Error uploading file!', error);
          this.notificationService.showError(error);
          this.tensileColumnValues = [];
          this.dataSource = new MatTableDataSource([]);
          this.tensileRawFileName = '';
          this.tensileResults = null;
          this.tensileRawUploadProgress = 0;
        },
      });
  }

  handleResponse(response: any): void {
    this.tensileResults = response.convertor_results;
    this.tensileColumnValues = response.convertor_results.df_results_cols;
    const jsonData = JSON.parse(response.convertor_results.df_results);
    const keys = Object.keys(jsonData[Object.keys(jsonData)[0]]);
    this.displayedColumns = ['specimen'].concat(keys);
    const tableData = Object.entries(jsonData).map(
      ([specimen, properties]: any) => ({ specimen, ...properties }),
    );
    this.dataSource = new MatTableDataSource(tableData);
    this.selectedDatetimeColumn =
      response.convertor_results.cols_names.col_name_date;
    this.selectedDirectionColumn =
      response.convertor_results.cols_names.col_name_direct;
    this.selectedLengthColumn =
      response.convertor_results.cols_names.col_name_length;
    this.selectedThicknessColumn =
      response.convertor_results.cols_names.col_name_thick;
    this.selectedWidthColumn =
      response.convertor_results.cols_names.col_name_width;
  }

  cancelUploading(type: string) {
    if (type === 'file') {
      this.tensileRawFileName = '';
      this.tensileFile = null;
      this.tensileColumnValues = [];
      this.dataSource = new MatTableDataSource([]);
      this.tensileResults = null;
      this.dataSheet = 0;
      this.nominalAge = 0;
      this.labReference = '';
      this.operator = '';
      this.preTreatement = '';
      this.timeZone = '';
    } else {
      this.uploadProgress = 0;
      this.totalFileSize = 0;
      this.showUploadButton = false;
    }
  }

  uploadFileToConvert() {
    this.graphLoader = true;
    const formData = new FormData();
    let metadataFile = this.selectedFile || '';

    if (this.rawFile) {
      formData.append('rawFile', this.rawFile, this.rawFile.name);
    }
    if (this.fitFile) {
      formData.append('fitFile', this.fitFile, this.fitFile.name);
    }

    this.dataSheetGenerateService
      .uploadFileToConvert(this.projectId, formData, metadataFile)
      .subscribe({
        next: (results: any) => {
          try {
            if (results) {
              this.flcParameters = results.convertor_results;
              this.flcParameters.plot_data.df_fit = JSON.parse(
                this.flcParameters.plot_data.df_fit,
              );
              this.flcParameters.plot_data.raw_points.x = JSON.parse(
                this.flcParameters.plot_data.raw_points.x,
              );
              this.flcParameters.plot_data.raw_points.y = JSON.parse(
                this.flcParameters.plot_data.raw_points.y,
              );
              this.flcParameters.plot_data.s_raw.x_data = JSON.parse(
                this.flcParameters.plot_data.s_raw.x_data,
              );
              this.flcParameters.plot_data.s_raw.y_data = JSON.parse(
                this.flcParameters.plot_data.s_raw.y_data,
              );
              this.showFlcPlot(
                this.flcParameters.plot_data.s_raw,
                this.flcParameters.plot_data.df_fit,
                this.flcParameters.plot_data.raw_points,
              );
            } else {
              this.graphLoader = false;
              this.notificationService.showError(results);
            }
          } catch (error) {
            this.graphLoader = false;
            console.error(error);
            this.notificationService.showError(error);
          }
        },
        error: (error: any) => {
          this.graphLoader = false;
          console.error(error);
          this.notificationService.showError(error);
        },
        complete: () => {
          this.graphLoader = false;
          console.error('File upload and processing completed.');
        },
      });
  }

  private showFlcPlot(
    sRaw: { x_data: any; y_data: any },
    dfFit: any,
    rawPoints: { x: any; y: any },
  ): void {
    this.graphLoader = true;
    // Transforming dfFit data
    const minorStrainFit = Object.values(dfFit['minor strain [-]']);
    const majorStrainFit = Object.values(dfFit['major strain [-]']);
    const sigmaPlus = Object.values(dfFit['+ sigma']);
    const sigmaMinus = Object.values(dfFit['- sigma']);

    // Transforming rawPoints data
    const xRaw = Object.values(rawPoints.x);
    const yRaw = Object.values(rawPoints.y);

    // Transforming sRaw data
    const xSRaw = Object.values(sRaw.x_data);
    const ySRaw = Object.values(sRaw.y_data);

    const traceRawGrouped: Partial<any> = {
      x: xRaw,
      y: yRaw,
      mode: 'markers',
      type: 'scatter',
      name: 'Mean test sample',
      marker: { color: 'black' },
    };

    const traceFit: Partial<any> = {
      x: minorStrainFit,
      y: majorStrainFit,
      mode: 'lines',
      type: 'scatter',
      name: 'FLC',
      line: { color: 'black', width: 3 },
    };

    const traceSigma: Partial<any> = {
      x: [...minorStrainFit, ...minorStrainFit.slice().reverse()],
      y: [...sigmaPlus, ...sigmaMinus.slice().reverse()],
      fill: 'toself',
      type: 'scatter',
      name: '±1σ',
      fillcolor: 'rgba(0,0,0,0.3)',
    };


    const layout: Partial<Plotly.Layout> = {
      title: 'FLC Data Visualization',
      xaxis: { title: 'Minor Strain [-]', zeroline: false },
      yaxis: { title: 'Major Strain [-]' },
      legend: {
        orientation: 'h',
        x: 0.5,
        y: -0.2,
        xanchor: 'center',
        yanchor: 'top',
      },
      margin: { t: 80, b: 100 },
    };

    const plotDiv = document.getElementById('flcPlotDiv');
    if (plotDiv) {
      this.graphLoader = false;
      Plotly.newPlot(
        plotDiv,
        [traceRawGrouped, traceFit, traceSigma],
        layout,
      ).catch((error) => {
        this.graphLoader = false;
        console.error('Error plotting FLC:', error);
        this.notificationService.showError(error);
      });
    } else {
      this.graphLoader = false;
      console.error('Element with id "flcPlotDiv" not found.');
    }
  }

  allFilesSelected() {
    return (
      this.rawFile instanceof File &&
      this.fitFile instanceof File &&
      this.selectedFile
    );
  }

  allFieldsSelected() {
    return (
      this.dataSheet &&
      this.nominalAge &&
      this.labReference !== '' &&
      this.operator !== '' &&
      this.preTreatement !== '' &&
      this.timeZone !== ''
    );
  }

  saveFLC() {
    this.saveFLCLoader = true;
    let object = {
      raw_file: this.flcParameters.raw_file,
      fit_file: this.flcParameters.fit_file,
      params: this.flcParameters.df_meta_data,
      deleteExistingSubFolder: this.deleteExistingSubFolder,
    };
    this.dataSheetGenerateService
      .saveFLCAscii(object, this.projectId)
      .subscribe({
        next: (response) => {
          if (response.ascii?.path) {
            this.saveFLCLoader = false;
            this.flcSavefilePath = true;
            this.toaster.success('Output save successfully ', '', {
              positionClass: 'custom-toast-position',
            });
          }
        },
        error: (error) => {
          console.error(error);
          this.saveFLCLoader = false;
          this.flcSavefilePath = false;
          this.notificationService.showError('Not able to save output');
        },
      });
  }

  navigate(pageName: string) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
  }

  tensileFileConvert(): void {
    let object = {
      tensile_file: this.tensileResults.tensile_file,
      params: {
        delete_existing: this.tensileDeleteExisting,
        cols_names: {
          col_name_date: this.selectedDatetimeColumn,
          col_name_direct: this.selectedDirectionColumn,
          col_name_length: this.selectedLengthColumn,
          col_name_thick: this.selectedThicknessColumn,
          col_name_width: this.selectedWidthColumn,
        },
        df_meta_data: {
          datasheet: this.dataSheet,
          nominal_age: this.nominalAge,
          lab_ref: this.labReference,
          operator: this.operator,
          pretreatement: this.preTreatement,
          time_zone: this.timeZone,
        },
      },
    };
    this.dataSheetGenerateService.tensileFileConvert(object).subscribe({
      next: (response) => {
        this.tensileResults = response.tensile_data;
        const jsonData = JSON.parse(response.tensile_data.df_results);
        const keys = Object.keys(jsonData[Object.keys(jsonData)[0]]);
        this.displayedColumns = ['specimen'].concat(keys);
        const tableData = Object.entries(jsonData).map(
          ([specimen, properties]: any) => {
            return { specimen, ...properties };
          },
        );
        this.dataSource = new MatTableDataSource(tableData);
      },
      error: (error) => {
        console.error(error);
        this.notificationService.showError(error);
      },
    });
  }

  saveTensileAscii(): void {
    this.saveTensileLoader = true;
    let object = {
      tensile_file: this.tensileResults.tensile_file,
      params: {
        delete_existing: this.tensileDeleteExisting,
        cols_names: {
          col_name_date: this.selectedDatetimeColumn,
          col_name_direct: this.selectedDirectionColumn,
          col_name_length: this.selectedLengthColumn,
          col_name_thick: this.selectedThicknessColumn,
          col_name_width: this.selectedWidthColumn,
        },
        df_meta_data: {
          datasheet: this.dataSheet,
          nominal_age: this.nominalAge,
          lab_ref: this.labReference,
          operator: this.operator,
          pretreatement: this.preTreatement,
          time_zone: this.timeZone,
        },
        df_results: this.tensileResults.df_results,
      },
    };
    this.dataSheetGenerateService
      .saveTensileAscii(object, this.projectId)
      .subscribe({
        next: (response) => {
          if (response.ascii?.path) {
            this.tensileSavefilePath = true;
            this.saveTensileLoader = false;
            this.toaster.success('Output save successfully ', '', {
              positionClass: 'custom-toast-position',
            });
          }
        },
        error: (error) => {
          console.error(error);
          this.tensileSavefilePath = false;
          this.saveTensileLoader = false;
          this.notificationService.showError('Not able to save output');
        },
      });
  }

  downloadZip(fileType: string) {
    let datasheet: string;
    let nominalAge: string;
    let saveFilePath: boolean;

    switch (fileType) {
      case 'Tensile':
        saveFilePath = this.tensileSavefilePath;
        datasheet = this.dataSheet.toString();
        nominalAge = this.nominalAge.toString();
        break;
      case 'FLC':
        saveFilePath = this.flcSavefilePath;
        datasheet = this.flcParameters.df_meta_data.datasheet.toString();
        nominalAge = this.flcParameters.df_meta_data.nominal_age.toString();
        break;
      default:
        return;
    }

    if (saveFilePath) {
      this.downloadFile(datasheet, nominalAge, fileType);
    }
  }

  private downloadFile(
    datasheet: string,
    nominalAge: string,
    fileType: string,
  ) {
    this.dataSheetGenerateService
      .downloadAscii(this.projectId, datasheet, nominalAge, fileType)
      .subscribe({
        next: (blob: Blob) =>
          this.handleBlob(blob, datasheet, nominalAge, fileType),
        error: (error: any) => {
          console.error('Download failed:', error);
          this.notificationService.showError(error);
        },
      });
  }

  private handleBlob(
    blob: Blob,
    datasheet: string,
    nominalAge: string,
    fileType: string,
  ) {
    const blobUrl = window.URL.createObjectURL(blob);
    const fileName = `${datasheet}_${fileType}_${nominalAge}_ASCII_export.zip`;
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
  }

  async onFolderDropped(event: DragEvent): Promise<void> {
    event.preventDefault();
    event.stopPropagation();
    this.uploadProgress = 0;
    this.showUploadButton = false;

    const items = event.dataTransfer?.items;
    if (items) {
      this.uploadFormData = new FormData();
      try {
        for (let i = 0; i < items.length; i++) {
          const entry = items[i].webkitGetAsEntry();
          if (entry) {
            if (entry.isDirectory) {
              const initialPath = `${entry.name}/`;
              await this.readDirectory(
                entry as FileSystemDirectoryEntry,
                initialPath,
                this.uploadFormData,
              );
            } else if (entry.isFile) {
              this.processFile(
                entry as FileSystemFileEntry,
                '',
                this.uploadFormData,
              );
            }
          }
        }
        this.showUploadButton = true;
      } catch (error) {
        console.error('Error processing files:', error);
        this.notificationService.showError(error);
        this.showUploadButton = false;
      }
    }
  }

  async readDirectory(
    directory: FileSystemDirectoryEntry,
    path: string,
    formData: FormData,
  ) {
    const reader = directory.createReader();
    let entries = await this.readAllEntries(reader);
    for (const entry of entries) {
      if (entry.isDirectory) {
        await this.readDirectory(
          entry as FileSystemDirectoryEntry,
          `${path}${entry.name}/`,
          formData,
        );
      } else if (entry.isFile) {
        this.processFile(entry as FileSystemFileEntry, path, formData);
      }
    }
  }

  async readAllEntries(
    reader: FileSystemDirectoryReader,
  ): Promise<FileSystemEntry[]> {
    let entries: any = [];
    let readEntries = async () => {
      const result = await new Promise<FileSystemEntry[]>((resolve) =>
        reader.readEntries(resolve),
      );
      if (result.length) {
        entries = entries.concat(result);
        await readEntries();
      }
    };
    await readEntries();
    return entries;
  }

  processFile(
    fileEntry: FileSystemFileEntry,
    path: string,
    formData: FormData,
  ) {
    fileEntry.file((file) => {
      formData.append('files', file, file.name);
      formData.append(
        'filePaths',
        this.dataSheetNumber + '/' + path + file.name,
      );
    });
  }

  onDirectorySelected(event: any) {
    const directory = event.target.files;
    this.uploadFormData = new FormData();
    this.uploadProgress = 0;
    for (let i = 0; i < directory.length; i++) {
      this.uploadFormData.append('files', directory[i], directory[i].name);
      this.uploadFormData.append(
        'filePaths',
        this.dataSheetNumber + '/' + directory[i].webkitRelativePath,
      );
    }
    this.showUploadButton = true;
    this.resetInput(event);
  }

  uploadDirectory() {
    this.uploadProgress = 0;
    let totalSize = 0;
    const siteId = '1';

    this.uploadFormData.forEach((value, key) => {
      if (value instanceof File) {
        totalSize += value.size;
      }
    });

    this.totalFileSize = totalSize;

    this.dataSheetGenerateService
      .ingestData(this.uploadFormData, siteId, this.projectId)
      .subscribe({
        next: (event) => {
          if (event.type === HttpEventType.UploadProgress) {
            this.uploadProgress = event.total
              ? Math.round((100 * event.loaded) / event.total)
              : this.uploadProgress;
          }
        },
        error: (error) => {
          console.error(error);
          this.notificationService.showError(error);
        },
        complete: () => {
          this.toaster.success('File Uploaded Successfully', '', {
            positionClass: 'custom-toast-position',
          });
        },
      });
  }
}
