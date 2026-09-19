import { Component, ElementRef, HostListener, Inject, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ApiService } from 'src/app/services/api.service';

@Component({
  selector: 'app-visualize-textdata',
  templateUrl: './visualize-textdata.component.html',
  styleUrls: ['./visualize-textdata.component.less'],
})
export class VisualizeTextdataComponent {
  private datasetId: string = '';
  textData: string = '';
  currentPage: number = 0;
  charCount: number = 20480;                                        // default char count of the page data.
  isAllPagesLoaded: boolean = false;
  isLoading: boolean = false;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private apiService: ApiService,
  ) {
    this.datasetId = data.datasetId;
  }

  ngOnInit() {
    this.fetchAndSetTextdata()
  }

  @ViewChild('scrollableDiv', { static: true }) scrollableDiv!: ElementRef;


  onScroll(): void {
    const element = this.scrollableDiv.nativeElement;
    const scrollPosition = element.scrollTop;
    const maxScroll = element.scrollHeight - element.clientHeight;
    const scrollPercentage = (scrollPosition / maxScroll) * 100;

    if (scrollPercentage > 50 && !this.isLoading) {
      this.fetchAndSetTextdata();
    }
  }

  /**
   * This method fetched paginated data if when the scroll bar reached 50% of the content, it will fetch nextpage
   * until the no pages left or any error occured in the backend.
   */

  fetchAndSetTextdata() {

    if (this.isAllPagesLoaded) return;
    this.currentPage += 1
    this.isLoading = true
    this.apiService
      .fetchTextDataset(this.datasetId, this.currentPage, this.charCount)
      .subscribe({
        next: (response) => {
          if (response.error_message) {
            this.isAllPagesLoaded = true
            return
          }
          this.textData = this.textData + response.file_data;
          if (response.next_page_number === this.currentPage) this.isAllPagesLoaded = true
          this.isLoading = false
        },
        error: (error) => {
          this.isAllPagesLoaded = true
        }
      });
  }

}
