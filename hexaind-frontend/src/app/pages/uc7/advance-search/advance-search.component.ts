import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatCheckboxChange } from '@angular/material/checkbox';

interface filtersModel{
  id:string,
  function:string,
  value:string,
  operator:string
}
@Component({
  selector: 'app-advance-search',
  templateUrl: './advance-search.component.html',
  styleUrls: ['./advance-search.component.less'],
})
export class AdvanceSearchComponent {
  constructor(
    public dialogRef: MatDialogRef<AdvanceSearchComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {}

  searchItems: string = '';
  itemsList: any[] = [];
  filteredItems: { name: string; selected: boolean }[] = [];
  selectAllItems: boolean = false;
  filters: filtersModel[] = [];
  functionList: string[] = ['contains', 'inverse'];
  operatorList: string[] = ['AND', 'OR'];
  dropdownType: string = '';

  filteredTopLevelKeys: string[] = [];

  ngOnInit(): void {
    this.itemsList = this.data['list'];
    this.dropdownType = this.data['dropdown'];
    this.addNewFilter();
    this.filteredItems = [...this.itemsList];
  }

  onSelectionChange(selectedItem: MatCheckboxChange, item: any): void {
    if (this.dropdownType !== 'traveler_id') {
      this.itemsList.forEach((item: any) => {
        if (item !== selectedItem) {
          item.selected = false;
        }
      });

      // Ensure that only one item is selected
      item.selected = selectedItem.checked;
    }
  }

  generateRandomCode(): string {
    const min = 0; // Minimum 4-digit number
    const max = 9999; // Maximum 4-digit number
    const code = Math.floor(Math.random() * (max - min + 1)) + min;
    return code.toString();
  }
  applyFiltersFunction() {
    this.filteredItems = [...this.itemsList];
    this.filteredItems = this.applyFilters(this.filteredItems, this.filters);
  }
  applyFilters(array: any[], filters: any[]): any[] {
    if (!Array.isArray(array) || !Array.isArray(filters)) {
      return [];
    }

    return array.filter((item) => {
      let condition = '';
      filters.forEach((filter, index) => {
        if (index > 0) {
          condition += ' ';
        }

        if (filter.function === 'contains') {
          condition += `item.name.includes('${filter.value}')`;
        }

        if (filter.function === 'inverse') {
          condition += `!item.name.includes('${filter.value}')`;
        }

        if (filter.operator && index < filters.length - 1) {
          condition += `${filter.operator === 'AND' ? ' &&' : ' ||'} `;
        }
      });

      // Evaluate the condition string safely
      try {
        const result = eval(condition);
        return result;
      } catch (error) {
        return false;
      }
    });
  }

  addNewFilter() {
    this.filters.push({
      id: this.generateRandomCode(),
      function: '',
      value: '',
      operator: '',
    });
  }
  removeFilter(id: any) {
    let index = this.filters.findIndex((filter: any) => filter.id == id);
    if (index != -1) {
      this.filters.splice(index, 1);
    }
  }
  toggleSelectAll() {
    this.selectAllItems = !this.selectAllItems;
    if (this.selectAllItems) {
      this.filteredItems = this.filteredItems.map((item: any) => {
        return {
          ...item, // Preserve other properties of the item
          selected: true, // Set the selected property to true
        };
      });
    } else {
      this.filteredItems = this.filteredItems.map((item: any) => {
        return {
          ...item, // Preserve other properties of the item
          selected: false, // Set the selected property to false
        };
      });
    }
  }
  filteredData() {
    return this.filteredItems.filter((item: any) =>
      item.name.toLowerCase().includes(this.searchItems.toLowerCase()),
    );
  }
  enableApplyButton() {
    return this.filteredItems.filter((item: any) => item.selected).length > 0
      ? false
      : true;
  }
  onApplyFilter() {
    let items = this.filteredItems
      .filter((item: any) => item.selected)
      .map((item: any) => item.name);
    this.dialogRef.close({ dataSelected: items, dropdown: this.data.dropdown });
  }

  onClose() {
    this.dialogRef.close();
  }

  resetAdvanceSearch() {
    this.filteredItems = [...this.itemsList];
    this.filters = [];
    this.addNewFilter();
  }
}
