import { Component, OnInit } from '@angular/core';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { DataSheetGenerateService } from '../data-sheet-generate.service';
import { MatDialog } from '@angular/material/dialog';
import { NotificationService } from '../notification.service';
NotificationService

@Component({
  selector: 'app-activity-logs',
  templateUrl: './activity-logs.component.html',
  styleUrls: ['./activity-logs.component.less']
})
export class ActivityLogsComponent implements OnInit {
  showMainHeader: boolean = false;
  toggleHeaderButton: string = 'expand_more';
  projectId!: string;
  originalDataSheetResults: any;
  correctedTensileFiles: string[] = [];
  selectedFile: string = '';
  displayedInitialFit: Record<string, any> | null = null;
  displayedNewFit: Record<string, any> | null = null;

  constructor(
    private configService: ConfigService,
    private datasheetService: DataSheetGenerateService,
    private router: Router,
    public dialog: MatDialog,
    private notificationService: NotificationService
  ) {
    const selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (selectedProjectId) {
      this.projectId = selectedProjectId;
    }
  }

  ngOnInit(): void {
    this.originalDataSheetResults = this.datasheetService.getActivityLogData();

    if (this.originalDataSheetResults) {
      const requestPayload = {
        project_id: this.projectId,
        datasheet: this.originalDataSheetResults.datasheetId,
        nominal_age: this.originalDataSheetResults.nominalAge,
      };

      this.fetchComparisonCorrectedTensile(requestPayload);
    }
  }

  async fetchComparisonCorrectedTensile(payload: Record<string, any>): Promise<void> {
    try {
      const response = await this.datasheetService.comparisonCorrectedTensileSample(payload);
      const sampleName = this.originalDataSheetResults.corrected_tensile_results?.sample_name;
      if (!sampleName) {
        return;
      }

      const correctData = response.correct_data;
      const allFileNames = [
        ...correctData.initial_fit_tensile.map((item: any) => this.extractFileName(item.file_name)),
        ...correctData.new_fit_tensile.map((item: any) => this.extractFileName(item.file_name))
      ];
      const uniqueFileNames = Array.from(new Set(allFileNames));
      this.correctedTensileFiles = uniqueFileNames;
      this.selectedFile = this.correctedTensileFiles[0];
      this.originalDataSheetResults.comparisonCorrectedTensileSample = { ...correctData };
      this.updateDisplayedData(this.selectedFile);
    } catch (error: any) {
      this.notificationService.showError(error);
    }
  }

  private extractFileName(filePath: string): string {
    return filePath.split('/').pop() || '';
  }

  onFileChange(selectedFile: string): void {
    this.selectedFile = selectedFile;
    this.updateDisplayedData(selectedFile);
  }

  updateDisplayedData(selectedFile: string): void {
    const { initial_fit_tensile, new_fit_tensile } = this.originalDataSheetResults.comparisonCorrectedTensileSample;
    this.displayedInitialFit = initial_fit_tensile.find((item: any) => this.extractFileName(item.file_name) === selectedFile) || null;
    this.displayedNewFit = new_fit_tensile.find((item: any) => this.extractFileName(item.file_name) === selectedFile) || null;
  }


  toggleMainHeader(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
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

  formatKey(key: string): string {
    return key
      .split('_')
      .map((word) => {
        if (word.toLowerCase() === 'grad') return 'Gradient';
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      })
      .join(' ');
  }

  getKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

}
