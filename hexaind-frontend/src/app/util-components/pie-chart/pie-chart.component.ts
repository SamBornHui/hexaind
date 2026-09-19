import { Component, Input, SimpleChanges } from '@angular/core';
import DataLabelsPlugin from 'chartjs-plugin-datalabels';


@Component({
  selector: 'app-pie-chart',
  templateUrl: './pie-chart.component.html',
  styleUrls: ['./pie-chart.component.less']
})
export class PieChartComponent {
  @Input() data: any;
  public pieChartLabels: string[] = ['Less', 'Better', 'Equal'];
  public pieChartPlugins = [DataLabelsPlugin];
  public pieChartData: any;
  public pieChartType: string = 'pie';
  public pieChartOptions: any = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'right', // Position of the legend
        labels: {
          usePointStyle: true,
        },
      },
      datalabels: {
        color: 'black', // Text color
        formatter: (value: any, ctx: any) => {
          return value + '%'; // Format the value
        },
      }
    },   
  };

  ngOnInit() { 
    this.pieChartData = {
      labels: this.pieChartLabels,
      datasets: [
        {
          data: this.data,
          backgroundColor: ['#FF5722', '#8BC34A', '#FFEB3B'], 
          borderWidth: 0
        },
      ],
    };
  }

  getPieChartAsBlob(): Promise<Blob | null> {
    return new Promise((resolve) => {
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (canvas) {
        canvas.toBlob((blob) => resolve(blob), 'image/png');
      } else {
        resolve(null);
      }
    });
  }
  
  async savePieChartAsImageAndGetTheUrl() {
    const blob = await this.getPieChartAsBlob()
    if(blob) {
      const url = URL.createObjectURL(blob);
      return url;
    }
    else {
      return ""
    }
  }

}

