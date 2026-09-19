import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'featureNameSearch',
  pure: false, // Setting pure to false ensures the pipe updates when the array changes.
})
export class FeatureNameSearchPipe implements PipeTransform {
  transform(items: any[], searchTerm: string): any[] {
    // Check if the items array and search term are valid
    if (!items || !searchTerm) {
      return items;
    }

    // Convert the search term to lowercase for case-insensitive matching
    searchTerm = searchTerm.toLowerCase();

    // Filter items based on the 'name' key
    return items.filter(item => {
      // Ensure the name exists and is a string before searching
      return item.name && item.name.toLowerCase().includes(searchTerm);
    });
  }
}
