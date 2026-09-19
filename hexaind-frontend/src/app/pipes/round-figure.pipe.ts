import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'roundFigure',
})
export class RoundFigurePipe implements PipeTransform {
  transform(value: any): any {
    if (typeof value === 'number') {
      return parseFloat(value.toFixed(4));
    }
    return value;
  }
}
