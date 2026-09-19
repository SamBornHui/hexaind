import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ButtonComponent } from '../button/button.component';
const fileTypeExtMap = new Map<string, string>([
  ['text/csv', '.csv'],
  ['text/plain', '.txt'],
  ['application/json', '.json'],
  ['application/xml', '.xml'],
  ['application/pdf', '.pdf'],
  ['application/msword', '.doc'],
  [
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.docx',
  ],
  ['application/vnd.ms-excel', '.xls'],
  [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xlsx',
  ],
  ['application/vnd.ms-powerpoint', '.ppt'],
  [
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.pptx',
  ],
  ['application/zip', '.zip'],
  ['application/x-tar', '.tar'],
  ['application/gzip', '.gz'],
  ['application/x-7z-compressed', '.7z'],
  ['application/vnd.rar', '.rar'],
  ['image/jpeg', '.jpg'],
  ['image/png', '.png'],
  ['image/gif', '.gif'],
  ['image/bmp', '.bmp'],
  ['image/svg+xml', '.svg'],
  ['image/webp', '.webp'],
  ['audio/mpeg', '.mp3'],
  ['audio/wav', '.wav'],
  ['audio/ogg', '.ogg'],
  ['video/mp4', '.mp4'],
  ['video/webm', '.webm'],
  ['video/x-msvideo', '.avi'],
  ['video/x-ms-wmv', '.wmv'],
  ['video/x-flv', '.flv'],
  ['video/quicktime', '.mov'],
  ['video/x-matroska', '.mkv'],
]);

@Component({
  selector: 'mst-file-upload',
  templateUrl: './file-upload.component.html',
  styleUrls: ['./file-upload.component.scss'],
  standalone: true,
  imports: [CommonModule, ButtonComponent],
})
export class FileUploadComponent {
  isDragging = false;
  @Input() fileExts: string[] = ['.csv'];
  @Output() filesSelected = new EventEmitter<File[]>();

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer) {
      const files = event.dataTransfer.files;
      this.addFiles(files);
    }
  }

  onFileSelected(event: any) {
    const files: FileList = event.target.files;
    this.addFiles(files);
  }

  addFiles(files: FileList) {
    const validFiles = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (this.isValidFile(file)) {
        validFiles.push(file);
      } else {
        // Handle invalid file types (e.g., show an error message)
        console.error('Invalid file type:', file.name, file.type);
      }
    }
    this.filesSelected.emit(validFiles);
  }

  getAcceptTypes(): string {
    return this.fileExts.map((ext) => fileTypeExtMap.get(ext)).join(',');
  }

  isValidFile(file: File): boolean {
    const ext = fileTypeExtMap.get(file.type) || '-';
    return this.fileExts.includes(ext);
  }
}
