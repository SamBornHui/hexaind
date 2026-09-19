import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-traveler-steps',
  templateUrl: './traveler-steps.component.html',
  styleUrls: ['./traveler-steps.component.less'],
})
export class TravelerStepsComponent {
  constructor(
    public dialogRef: MatDialogRef<TravelerStepsComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {}

  jsonData: any = {};
  topLevelKeys: string[] = [];
  categoriesMap: { [key: string]: string[] } = {};
  selectedCategories: { [key: string]: { [category: string]: boolean } } = {};
  selectedTopLevelKeys: { [key: string]: boolean } = {};

  suffixes: string[] = [];
  selectedSuffixes: string[] = [];
  filteredSuffixes: string[] = [];

  allItems: { [key: string]: boolean } = {};
  filteredItems: { [key: string]: boolean } = {};

  selectAllTopLevelKeys: boolean = false;
  selectAllSuffixes: boolean = false;
  selectAllItems: boolean = false;

  searchTopLevelKeys: string = '';
  searchSuffixes: string = '';
  searchItems: string = '';

  filteredTopLevelKeys: string[] = [];
  searchText:boolean = false;

  ngOnInit(): void {
    this.jsonData = this.data['list'];
    this.topLevelKeys = Object.keys(this.jsonData);
    this.filteredTopLevelKeys = this.topLevelKeys;

    this.topLevelKeys.forEach((key) => {
      this.categoriesMap[key] = Object.keys(this.jsonData[key]);
      this.selectedCategories[key] = {};
      this.categoriesMap[key].forEach((category) => {
        this.selectedCategories[key][category] = false;
      });
    });

    this.suffixes = this.extractUniqueSuffixes();
    this.filteredSuffixes = this.suffixes;
    this.updateAllItems();
    if (this.data['selectedList'] && this.data['selectedList'].length > 0) {
      this.setSelectedTravelerSteps();
    }
    this.filteredItems = { ...this.allItems };
    if(this.data['selectDropDown'] == 'travelerid'){
      this.resetTravelerSteps();
      this.data['selectDropDown'] = '';
    }
  }

  setSelectedTravelerSteps() {
    this.data['selectedList'].forEach((step: any) => {
      if (this.allItems.hasOwnProperty(step)) this.allItems[step] = true;
    });
  }

  onTopLevelKeyChange(key: string, checked: boolean): void {
    this.categoriesMap[key].forEach((category) => {
      this.selectedCategories[key][category] = checked;
      this.updateItemsBasedOnCategory(key, category, checked);
    });
    //this.updateSuffixesBasedOnTopLevelKey(key, checked);
    this.updateItemsBasedOnTopLevelKey(key, checked);
  }

  updateSuffixesBasedOnTopLevelKey(key: string, checked: boolean): void {
    const suffixSet = new Set<string>();
    if (checked && this.jsonData[key]) {
      Object.keys(this.jsonData[key]).forEach((category) => {
        this.jsonData[key][category].forEach((item: string) => {
          const suffix = item.split('-')[1]?.split(' ')[0];
          if (suffix) suffixSet.add(suffix);
        });
      });
      this.selectedSuffixes = Array.from(suffixSet);
    } else {
      this.selectedSuffixes = [];
    }
    this.updateItemsSelectionBasedOnSuffix();
  }

  updateItemsBasedOnTopLevelKey(key: string, checked: boolean): void {
    if (this.jsonData[key]) {
      this.categoriesMap[key].forEach((category) => {
        this.jsonData[key][category]?.forEach((item: string) => {
          this.allItems[item] = checked;
        });
      });
    }
  }

  updateItemsBasedOnCategory(
    key: string,
    category: string,
    checked: boolean,
  ): void {
    if (this.jsonData[key] && this.jsonData[key][category]) {
      this.jsonData[key][category].forEach((item: string) => {
        if (checked) {
          this.allItems[item] = true;
        } else {
          this.allItems[item] = false;
        }
      });
    }
    this.filterItems();
  }

  updateSuffixAndItemsBasedOnCategory(
    key: string,
    category: string,
    checked: boolean,
  ): void {
    this.jsonData[key][category].forEach((item: string) => {
      const suffix = item.split('-')[1]?.split(' ')[0];
      if (suffix) {
        if (checked && !this.selectedSuffixes.includes(suffix)) {
          this.selectedSuffixes.push(suffix);
        } else if (!checked) {
          this.selectedSuffixes = this.selectedSuffixes.filter(
            (s) => s !== suffix,
          );
        }
      }
      this.allItems[item] = checked;
    });
    this.updateItemsSelectionBasedOnSuffix();
  }

  extractUniqueSuffixes(): string[] {
    const suffixSet = new Set<string>();
    Object.values(this.jsonData).forEach((categories: any) => {
      Object.values(categories)
        .flat()
        .forEach((item: any) => {
          const suffix = item.split('-')[1]?.split(' ')[0];
          if (suffix) suffixSet.add(suffix);
        });
    });
    return Array.from(suffixSet);
  }

  updateAllItems(): void {
    this.allItems = {};
    Object.keys(this.jsonData).forEach((key) => {
      Object.keys(this.jsonData[key]).forEach((category) => {
        this.jsonData[key][category].forEach((item: string) => {
          this.allItems[item] = false;
        });
      });
    });
  }

  toggleSelectAllTopLevelKeys(): void {
    this.selectAllTopLevelKeys = !this.selectAllTopLevelKeys;
    this.filteredTopLevelKeys.forEach((key) => {
      this.selectedTopLevelKeys[key] = this.selectAllTopLevelKeys;
      this.categoriesMap[key].forEach((category) => {
        this.selectedCategories[key][category] = this.selectAllTopLevelKeys;
        this.updateSuffixAndItemsBasedOnCategory(
          key,
          category,
          this.selectAllTopLevelKeys,
        );
      });
    });

    this.selectedSuffixes = this.selectAllTopLevelKeys
      ? this.extractUniqueSuffixes()
      : [];
    this.selectAllSuffixes = this.selectAllTopLevelKeys;
    this.selectAllItems = this.selectAllTopLevelKeys;
    this.updateItemsSelectionBasedOnSuffix();
  }

  toggleSelectAllSuffixes(): void {
    this.selectAllSuffixes = !this.selectAllSuffixes;
    this.selectedSuffixes = this.selectAllSuffixes
      ? [...this.filteredSuffixes]
      : [];
    this.updateItemsSelectionBasedOnSuffix();
    this.selectAllItems = Object.keys(this.allItems).every((item) => {
      const itemSuffix = item.split('-')[1]?.split(' ')[0];
      return this.selectedSuffixes.includes(itemSuffix);
    });
  }

  toggleSelectAllItems(): void {
    this.selectAllItems = !this.selectAllItems;
    Object.keys(this.allItems).forEach((item) => {
      if (this.filteredItems[item] !== undefined) {
        this.allItems[item] = this.selectAllItems;
      }
    });
    this.filterItems();
  }

  onSuffixChange(suffix: string, checked: boolean): void {
    if (checked) {
      this.selectedSuffixes.push(suffix);
    } else {
      this.selectedSuffixes = this.selectedSuffixes.filter((s) => s !== suffix);
    }
    this.updateItemsSelectionBasedOnSuffix();
  }

  updateItemsSelectionBasedOnSuffix(): void {
    Object.keys(this.allItems).forEach((item) => {
      const itemSuffix = item.split('-')[1]?.split(' ')[0];
      if (this.selectedSuffixes.length === 0) {
        this.allItems[item] = false;
      } else if (this.allItems[item] !== true) {
        this.allItems[item] = itemSuffix
          ? this.selectedSuffixes.includes(itemSuffix)
          : false;
      }
    });
    this.filterItems();
  }

  // filterItems(): void { console.log(this.allItems,"serach functionality travelers");
  //   this.filteredItems = Object.keys(this.allItems)
  //     .filter((item) =>
  //       item.toLowerCase().includes(this.searchItems.toLowerCase()),
  //     )
  //     .reduce(
  //       (obj, key) => {
  //         obj[key] = this.allItems[key];
  //         return obj;
  //       },
  //       {} as { [key: string]: boolean },
  //     );
  // }

  filterItems(): void {
    console.log(this.allItems, "search functionality travelers");
  
    // Split the search expression into AND (`&`) and OR (`|`) terms
    const searchTerms = this.searchItems.split('|').map((orTerm) =>
      orTerm.split('&').map((andTerm) => andTerm.trim().toLowerCase())
    );
  
    this.filteredItems = Object.keys(this.allItems)
      .filter((item) => {
        const itemLower = item.toLowerCase();
  
        // Check each OR condition
        return searchTerms.some((andTerms) =>
          // Check all AND conditions within the OR condition
          andTerms.every((term) => itemLower.includes(term))
        );
      })
      .reduce(
        (obj, key) => {
          obj[key] = this.allItems[key];
          return obj;
        },
        {} as { [key: string]: boolean },
      );
  
    console.log(this.filteredItems, "Filtered items based on search");
  }
  

  filterSuffixes(): void {
    this.filteredSuffixes = this.suffixes.filter((suffix) =>
      suffix.toLowerCase().includes(this.searchSuffixes.toLowerCase()),
    );
  }

  onSearchSuffixes(): void {
    this.filterSuffixes();
    if (this.searchSuffixes === '') {
      if (this.filteredSuffixes.length != this.selectedSuffixes.length) {
        this.selectAllSuffixes = false;
      }
    }
  }

  onSearchItems(): void {
    if (this.searchItems === '') {
      this.selectAllItems = Object.values(this.allItems).every(
        (value) => value === true,
      );
    }
    this.filterItems();
  }

  filterTopLevelKeys(): void { console.log(this.topLevelKeys,"traveler keys");
    this.filteredTopLevelKeys = this.topLevelKeys.filter((key) =>
      key.toLowerCase().includes(this.searchTopLevelKeys.toLowerCase()),
    );
  }

  onSearchTopLevelKeys(): void {
    this.filterTopLevelKeys();
    if (this.searchTopLevelKeys === '') {
    }
  }

  getAllItemKeys(): string[] {
    return Object.keys(this.filteredItems);
  }

  onItemChange(item: string, checked: boolean): void {
    this.allItems[item] = checked;

    const reverse_map_of_modules: { [key: string]: string } = {};

    Object.keys(this.selectedCategories).forEach((key) => {
      Object.keys(this.selectedCategories[key]).forEach((innerKey) => {
        reverse_map_of_modules[innerKey] = key;
      });
    });

    // if item.split('-')[1]?.split(' ')[0]
    if (
      item.split('-')[0] &&
      reverse_map_of_modules.hasOwnProperty(item.split('-')[0])
    ) {
      const module_id = item.split('-')[0];
      const category = reverse_map_of_modules[module_id];
      if (
        checked == false &&
        this.selectedCategories[category][module_id] == true
      ) {
        this.selectedCategories[category][module_id] = false;
      } else {
        if (checked == true) {
          //
        }
      }
    }

    const loopsId: any = item.split('-')[1]?.split(' ')[0];
    this.selectedSuffixes.forEach((suffix) => {
      if (suffix == loopsId) {
        let index = this.selectedSuffixes.indexOf(suffix);
        if (index > -1) {
          this.selectedSuffixes.splice(index, 1);
        }
      }
    });
    this.filterItems();
  }

  isAllSelected(key: string): boolean {
    const categories = this.categoriesMap[key];
    return categories.every(
      (category) => this.selectedCategories[key][category],
    );
  }

  onCategoryChange(key: string, category: string, checked: boolean): void {
    // console.log("this.updateItemsBasedOnTopLevelKey(key, checked); ", this.selectedCategories[key][category])
    this.selectedCategories[key][category] = checked;
    // console.log("this.allItems[category]: ",this.allItems[key])
    // this.allItems[key] = checked;
    // Update items based on the category change
    this.updateItemsBasedOnCategory(key, category, checked);
    //this.filterItems();
  }

  getSelectedTravelerSteps() {
    return Object.keys(this.filteredItems).filter(
      (item) => this.filteredItems[item],
    );
  }

  onClose() {
    this.dialogRef.close();
  }

  saveTravelerSteps() {
    let result = Object.keys(this.filteredItems).filter(
      (item) => this.filteredItems[item],
    );
    this.dialogRef.close({ success: true, selectedTravelerStep: result });
  }

  resetTravelerSteps() { console.log("get set status");
    // this.toggleSelectAllTopLevelKeys()
    this.selectAllTopLevelKeys = false;
    this.selectAllSuffixes = false;
    this.selectAllItems = false;
    this.selectedSuffixes = [];
    this.uncheckAllCategories(this.selectedCategories);
    this.uncheckAllTopLevelKeys(this.selectedTopLevelKeys);
    this.uncheckAllTopLevelKeys(this.filteredItems);
    this.data['selectDropDown'] = [];
    console.log(this.data['selectDropDown'],"select drop down");
  }

  uncheckAllTopLevelKeys(topkeys: any) {
    Object.keys(topkeys).forEach((key) => {
      topkeys[key] = false;
    });
  }

  uncheckAllCategories(inputObj: any): void {
    Object.keys(inputObj).forEach((key) => {
      if (typeof inputObj[key] === 'object') {
        this.uncheckAllCategories(inputObj[key]);
      } else {
        inputObj[key] = false;
      }
    });
  }

  addName() {
    let allTravelerSteps = this.getAllItemKeys();
    if (this.searchItems && !allTravelerSteps.includes(this.searchItems)) {      
      this.allItems[this.searchItems] = true;
      console.log(this.filteredItems, this.allItems);
      this.clearSearch();
    }

  }
  clearSearch() {
    this.searchItems = '';
    this.filterItems();
    this.onSearchItems();
  }
}
