import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-privacy-policy',
  templateUrl: './privacy-policy.component.html',
  styleUrls: ['./privacy-policy.component.less']
})
export class PrivacyPolicyComponent {
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
