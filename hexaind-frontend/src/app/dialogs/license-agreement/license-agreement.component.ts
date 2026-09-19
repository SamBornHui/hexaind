import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-license-agreement',
  templateUrl: './license-agreement.component.html',
  styleUrls: ['./license-agreement.component.less']
})
export class LicenseAgreementComponent {
  @Output() requestClose = new EventEmitter<void>();

  ngAfterViewInit() {
    this.setScrollTop();
  }

  setScrollTop() {
    let myDiv: HTMLElement | null = document.getElementById('myDiv');

    if(myDiv) {
      console.log("YES mydiv");
        myDiv.scrollTop = 0;
       // myDiv.scrollIntoView(true);
    } else {
      console.log("NO myDiv");
    }
  }

  onCloseRequest(): void {
    this.requestClose.emit();
  }
}
