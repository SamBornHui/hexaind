import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-uc6',
  templateUrl: './uc6.component.html',
  styleUrls: ['./uc6.component.less']
})
export class Uc6Component {
  iframeUrl: SafeResourceUrl | undefined;

  constructor(private sanitizer: DomSanitizer){}

  ngOnInit(): void{
    const url = 'https://azldspock01:8050';
    this.iframeUrl =  this.sanitizer.bypassSecurityTrustResourceUrl(url)
  }
}
