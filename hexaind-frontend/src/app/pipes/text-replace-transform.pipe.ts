import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'replaceAndCapitalize',
})
export class ReplaceAndCapitalizePipe implements PipeTransform {
  transform(value: any): any {
    value = value.replace(/_/g, ' ').replace(/-/g, ' ');
    value = value.replace(/\b\w/g, function (match: string) {
      return match.toUpperCase();
    });
    return value;
  }
}
