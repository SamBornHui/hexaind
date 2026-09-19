import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-uc12',
  templateUrl: './uc12.component.html',
  styleUrls: ['./uc12.component.less']
})
export class Uc12Component {
  iframeUrl: SafeResourceUrl | undefined;

  constructor(private sanitizer: DomSanitizer){}

  ngOnInit(): void{
    const url = 'http://azldspock01.az.micron.com:8891/uc12'
    this.iframeUrl =  this.sanitizer.bypassSecurityTrustResourceUrl(url)
  }
}
