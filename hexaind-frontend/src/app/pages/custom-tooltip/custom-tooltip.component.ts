import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-custom-tooltip',
  templateUrl: './custom-tooltip.component.html',
  styleUrls: ['./custom-tooltip.component.less'],
})
export class CustomTooltipComponent implements OnInit {
  @Input() tooltipContent!: any;
  ngOnInit(): void {}

  get purpose(): string {
    return this.tooltipContent ? this.tooltipContent.purpose || 'N/A' : 'N/A';
  }

  get input(): string {
    return this.tooltipContent ? this.tooltipContent.input || 'N/A' : 'N/A';
  }

  get output(): string {
    return this.tooltipContent ? this.tooltipContent.output || 'N/A' : 'N/A';
  }

  get description(): string {
    return this.tooltipContent ? this.tooltipContent.description || 'N/A' : 'N/A';
  }

  get showDescription(): boolean{
    return (this.tooltipContent?.description)?true:false;
  }
}
