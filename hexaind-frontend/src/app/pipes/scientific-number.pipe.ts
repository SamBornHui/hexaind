import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'scientificNumber',
})
export class ScientificNumberPipe implements PipeTransform {
  transform(value: number, forceScientific: boolean = false): string {
    if (value === undefined || value === null) {
      return 'null';
    }
    if (typeof value !== 'number' || isNaN(value)) {
      return value.toString();
    }

    if (value === 0) {
      return '0';
    }
    
    if (forceScientific) {
      return this.formatScientific(value.toExponential(3));
    }
    // Logic for negative values
    if (value < 0.00010) { 
      if (value > -0.00010) {
        return value.toExponential(3);
      } else if (value > -100_000) {
        return parseFloat(value.toFixed(4)).toString();
      } else if (value > -1_000_000_000) {
        return parseFloat(value.toFixed(2)).toString();
      } else {
        return value.toExponential(3).replace('+', '');
      }
    }

    // Logic for positive values
    if (value >= 0.00010) { 
      if (value < 100_000) {
        return parseFloat(value.toFixed(4)).toString();
      } else if (value < 1_000_000_000) {
        return parseFloat(value.toFixed(4)).toString();
      } else {
        return value.toExponential(4).replace('+', '');
      }
    } else {
      return value.toExponential(4).replace('+', '');
    }
  }

  private formatScientific(exponentialStr: string): string {
    const [coefficient, exponent] = exponentialStr.split('e');
    if (exponent === '0') {
      return `${coefficient} × 10⁰`;
    }
    const formattedExponent = this.convertToSuperscript(exponent.replace('+', ''));
    return `${coefficient} × 10${formattedExponent}`;
  }

  private convertToSuperscript(exponent: string): string {
    const superscriptMap: { [key: string]: string } = {
      '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
      '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
      '-': '⁻'
    };
    return exponent.split('').map(char => superscriptMap[char] || char).join('');
  }
}