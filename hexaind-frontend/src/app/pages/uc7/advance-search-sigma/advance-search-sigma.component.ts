import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { DataCatalogService } from '../../tools/data-catalog/data-catalog.service';
import { ToastrService } from 'ngx-toastr';

interface filtersModel{
  id:string,
  function:string,
  value:string,
  operator:string
}
@Component({
  selector: 'app-advance-search-sigma',
  templateUrl: './advance-search-sigma.component.html',
  styleUrls: ['./advance-search-sigma.component.less'],
})
export class AdvanceSearchSigmaComponent {
  selectedFromFilteredItems: string[] | undefined;
  transformedFilters: any;
  selectedFilterValues: any[] = [];
  selected_path_query: any;
  
  constructor(
    private dataCatService: DataCatalogService,
    public dialogRef: MatDialogRef<AdvanceSearchSigmaComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public toaster: ToastrService,
  ) {

  }

  searchItems: string = '';
  searchSelectItems: string = '';
  itemsList: any[] = [];
  filteredItems: { name: string; selected: boolean }[] = [];
  selectedItems: { name: string; selected: boolean }[] = [];
  selectAllItems: boolean = false;
  selectedAllItems: boolean = true;
  filters: filtersModel[] = [];
  searchQueryItem: any[] | undefined;
  functionList: { name: string; value: string }[] = [
    { name: 'contains', value: 'LQ' },
    { name: 'inverse', value: 'NLQ' },
    { name: 'Equal', value: 'EQ' },        // Equal corresponds to 'EQ'
    { name: 'Not Equal', value: 'NE' },
    { name: 'Between', value: 'BW' }
  ];
  
  operatorList: string[] = ['AND', 'OR', 'XOR'];
  dropdownType: string = '';

  filteredTopLevelKeys: string[] = [];
  responsePathRun : any;
  runStepGQLFileList: any = [];
  uc2SigmaSelectedData: any = {
    measurement_steps: {
      file_path: '',
      selected_values: [],
    },
    run_parameters: {
      file_path: '',
      selected_values: [],
    },
    point_steps: {
      file_path: '',
      selected_values: [],
    },
    measurement_parameters: {
      file_path: '',
      selected_values: [],
    },
    point_parameters: {
      file_path: '',
      selected_values: [],
    },
    wafer_parameters: {
      file_path: '',
      selected_values: [],
    },
    gql_file_details: {
      parquet_file_path: '',
      gql_file_path: '',
    },
  };

  runParametersSearch: any;
  isUC2SigmaRunParametersSelectAll: boolean = false;
  UC2SigmaSelectedRunParameters: any = [];
  selectedPage: number = 1;

  totalItems: number = 100; 
  itemsPerPage: number = 1000; 
  totalPages: number | undefined;

  showLoader:boolean = false;

  searchSelectedItems: string = ''; 
  selectedItemsPage: number = 1;
  totalSelectedItems: number = 100;
  totalSelectedItemsPages: number = 100; 
  selectedItemsPerPage: number = 1000; 

  paginatedSelectedItems: any[] = [];

  selectedItemsArray: string[] = [];

  selectedItemsMap: { [pageIndex: number]: { name: string; selected: boolean }[] } = {}; 

  selected_path: string | null = null;

  ngOnInit(): void { 
    this.addNewFilter();
    this.onUC2GenerateUniquesPagination(1);
    this.onUC2GenerateUniquesPaginationSelected(1);
    this.onSelectedItemsPagination(this.selectedItemsPage);
  }

  onSelectionChange(selectedItem: MatCheckboxChange, item: any): void { 
      this.filteredItems.forEach((item: any) => {
        if (item !== selectedItem) {
          item = false;
        }
      });
      item = selectedItem.checked;
  }

  generateRandomCode(): string {
    const min = 0; 
    const max = 9999; 
    const code = Math.floor(Math.random() * (max - min + 1)) + min;
    return code.toString();
  }

  async applyFiltersFunction() {
    
    this.showLoader = true;
    this.filteredItems = this.filteredItems.map((item: any) => item);    
    this.filteredItems = this.applyFilters(this.filteredItems, this.filters);

    const pageDetails = {
      pageIndex: 0, 
      pageSize: 10, 
    };

    try {
      const res = await this.dataCatService.getQueryUniques(this.data.path, 'run_parameters', pageDetails, this.filters).toPromise();
      if (res.body['uniques']) { 
        this.showLoader = false;
        this.filteredItems = res.body['uniques'].map((item: string) => ({
          name: item,     
          selected: false 
        }));

        this.totalItems = res.body['rows_count'];
        this.totalPages = Math.max(Math.ceil(this.totalItems / this.itemsPerPage), 1);
        this.uc2SigmaSelectedData.run_parameters.file_path = this.data.path;
        this.runParametersSearch = this.filteredItems;
  
       
        this.isUC2SigmaRunParametersSelectAll =
        this.filteredItems.length === this.UC2SigmaSelectedRunParameters.length;
      }
    
    } catch (error) {
    this.toaster.error('Error in fetching data');
    console.error('Error in pagination fetch:', error);
    }
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
        this.filteredItems = this.filteredItems.map(item => ({
            ...item,
            selected: true
        }));
    } else {
        this.filteredItems = this.filteredItems.map(item => ({
            ...item,
            selected: false
        }));
    }

    this.selectedItemsMap[this.selectedPage] = [...this.filteredItems];
  }

  
  getSelectedItems() {
      const allSelectedItems = Object.values(this.selectedItemsMap)
          .flat() 
          .filter(item => item.selected); 
      return allSelectedItems;
  }
  filteredData() {
    return this.filteredItems.filter((item: any) =>
      item.toLowerCase().includes(this.searchItems.toLowerCase()),
    );
  }

  onSearch() {
    if (this.searchItems) {
      // Call your filtering function or any other logic here
      this.filterItems();
    }
  }

  async filterItems() {
    if (!this.searchItems || this.searchItems.trim() === '') {
      this.onUC2GenerateUniquesPagination(1);
    } else {
      const searchQuery = this.searchItems;

      const pageDetails = {
        pageIndex: 0, 
        pageSize: 10, 
      };

      //this.searchQueryItem =  await this.dataCatService.getQueryUniques(this.data.path, 'run_parameters', pageDetails, 'search', searchQuery).toPromise();

      try {
        const res = await this.dataCatService.getQueryUniques(this.data.path, 'run_parameters', pageDetails, 'search', searchQuery).toPromise();
        if (res.body['uniques']) { 
          this.showLoader = false;
          this.filteredItems = res.body['uniques'].map((item: string) => ({
            name: item,     
            selected: false 
          }));
  
          this.totalItems = res.body['rows_count'];
          this.totalPages = Math.max(Math.ceil(this.totalItems / this.itemsPerPage), 1);
          this.uc2SigmaSelectedData.run_parameters.file_path = this.data.path;
          this.runParametersSearch = this.filteredItems;
    
         
          this.isUC2SigmaRunParametersSelectAll =
          this.filteredItems.length === this.UC2SigmaSelectedRunParameters.length;
        }
      
      } catch (error) {
      this.toaster.error('Error in fetching data');
      console.error('Error in pagination fetch:', error);
      }
    }
  }


  onSelectSearch() {
    if (this.searchSelectItems) {
      // Call your filtering function or any other logic here
      this.filterSelectSearchItems();
    }
  }

  async filterSelectSearchItems() {
    if (!this.searchSelectItems || this.searchSelectItems.trim() === '') {
      this.onUC2GenerateUniquesPaginationSelected(1);
    } else {
      const searchQuery = this.searchSelectItems;

      const pageDetails = {
        pageIndex: 0, 
        pageSize: 10, 
      };

      //this.searchQueryItem =  await this.dataCatService.getQueryUniques(this.data.path, 'run_parameters', pageDetails, 'search', searchQuery).toPromise();

      try {
        const res = await this.dataCatService.getQueryUniquesAdvanced(this.data.selectedPath, 'run_parameters', pageDetails, this.data.selectedPath,'search', searchQuery).toPromise();
        if (res.body['uniques']) {
          this.selectedFilterValues = res.body['uniques'].map((item: string) => ({
              name: item,
              selected: true // Mark as selected
          }));
          console.log(this.selectedFilterValues, "Selected Filter Values");

          this.totalSelectedItems = res.body['rows_count'];
          this.totalSelectedItemsPages = Math.max(Math.ceil(this.totalSelectedItems / this.selectedItemsPerPage), 1);

      }
      
      } catch (error) {
      this.toaster.error('Error in fetching data');
      console.error('Error in pagination fetch:', error);
      }
    }
  }
  

  enableApplyButton() { 
    const hasFilteredSelection = this.filteredItems.some((item: any) => item.selected === true || item.selected === false);
    // const hasSelectedListChanges = this.data.selectedList.some((item: any) => item.selected === true || item.selected === false || item.checked === true || item.checked === false);
    const hasSelectedListChanges = 
  this.data.selectedList.length > 0 && 
  this.data.selectedList.some((item: any) => 
    item.selected === true || 
    item.selected === false || 
    item.checked === true || 
    item.checked === false
  );
  
    return !(hasFilteredSelection || hasSelectedListChanges);
  }
  
  
  async onApplyFilter() { 

    const pageDetails = {
      pageIndex: 0, 
      pageSize: 10, 
    };

    const hasEmptyValue = this.filters.some(filterItem => !filterItem.value);
    console.log(this.selected_path_query,"set path values");
    if(this.selected_path_query != undefined){
      this.selected_path = this.selected_path_query;
    }else{ console.log(this.data.selectedPath,"set path values1");
      this.selected_path = this.data.selectedPath !== undefined ? this.data.selectedPath : null;
    }
    if (this.selectAllItems && this.searchItems === '' && hasEmptyValue && this.selectedAllItems && this.searchSelectItems == '') {
        this.filters = []; 
        
        try {
            const res = await this.dataCatService.getSelectQueryUniques(
                this.data.path,
                this.data.dropdown,
                pageDetails,
                this.filters,
                'ALL',
                this.selected_path
            ).toPromise();

            if (res && res.body['selected_path']) {
                this.selected_path = res.body['selected_path'];
            }
        } catch (error) {
            this.toaster.error('Error in fetching data');
            console.error('Error in pagination fetch:', error);
        }
    } else if (this.selectAllItems && this.searchItems !== '' && hasEmptyValue && this.selectedAllItems && this.searchSelectItems == '') {
      
        this.filters = []; 

        try {
          const res = await this.dataCatService.getSelectQueryUniques(
              this.data.path,
              this.data.dropdown,
              pageDetails,
              this.filters,
              'QUERY',
              this.selected_path,
              this.searchItems
          ).toPromise();

          if (res && res.body['selected_path']) {
              this.selected_path = res.body['selected_path'];
          }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
        
    } else if (!this.selectAllItems && this.searchItems !== '' && hasEmptyValue && this.selectedAllItems && this.searchSelectItems == '') {
      this.filters = []; 
      this.selectedFromFilteredItems = this.filteredItems
      .filter(item => item.selected === true)  // Filter only selected items
      .map(item => item.name);  // Extract only the 'name' property

      try {
        const res = await this.dataCatService.getSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'MANUAL',
            this.selected_path,
            this.searchItems,
            this.selectedFromFilteredItems
        ).toPromise();

        if (res && res.body['selected_path']) {
            this.selected_path = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
        
    } else if (!this.selectAllItems && this.searchItems === '' && !hasEmptyValue && this.selectedAllItems && this.searchSelectItems == '') {
      this.selectedFromFilteredItems = this.filteredItems
      .filter(item => item.selected === true)  // Filter only selected items
      .map(item => item.name);  // Extract only the 'name' property
        this.transformedFilters = this.filters.map((filterItem: { function: string; value: string | string[]; operator: string }, index: number) => {
          const column = index === 0 ? "run_parameters" : `run_parameters`; 
          
          return [
            column,
            {
              operation: filterItem.function, 
              value: typeof filterItem.value === 'string' ? filterItem.value : filterItem.value.join(', '), 
            },
            filterItem.operator 
          ];
        });
        try {
          const res = await this.dataCatService.getSelectQueryUniques(
              this.data.path,
              this.data.dropdown,
              pageDetails,
              this.transformedFilters,
              'MANUAL',
              this.selected_path,
              this.searchItems,
              this.selectedFromFilteredItems
          ).toPromise();
  
          if (res && res.body['selected_path']) {
              this.selected_path = res.body['selected_path'];
          }
        } catch (error) {
            this.toaster.error('Error in fetching data');
            console.error('Error in pagination fetch:', error);
        }
        
    }else if (this.selectAllItems && this.searchItems === '' && !hasEmptyValue && this.selectedAllItems && this.searchSelectItems == '') {
      
        this.transformedFilters = this.filters.map((filterItem: { function: string; value: string | string[]; operator: string }, index: number) => {
          const column = index === 0 ? "run_parameters" : `run_parameters`; 
          
          return [
            column,
            {
              operation: filterItem.function, 
              value: typeof filterItem.value === 'string' ? filterItem.value : filterItem.value.join(', '), 
            },
            filterItem.operator 
          ];
        });
        try {
          const res = await this.dataCatService.getSelectQueryUniques(
              this.data.path,
              this.data.dropdown,
              pageDetails,
              this.transformedFilters,
              'QUERY',
              this.selected_path,
              this.searchItems,
              this.selectedFromFilteredItems
          ).toPromise();
  
          if (res && res.body['selected_path']) {
              this.selected_path = res.body['selected_path'];
          }
        } catch (error) {
            this.toaster.error('Error in fetching data');
            console.error('Error in pagination fetch:', error);
        }
        
    }else if (!this.selectAllItems && this.searchItems === '' && hasEmptyValue && this.selectedAllItems && this.searchSelectItems == '') { 
      this.filters = [];
      this.selectedFromFilteredItems = this.filteredItems
      .filter(item => item.selected === true)  // Filter only selected items
      .map(item => item.name);  // Extract only the 'name' property
      console.log(this.selectedFromFilteredItems,"filkters");
      if (this.selectedFromFilteredItems.length === 0) {
        this.selectedFromFilteredItems = this.selectedFilterValues
      .filter(item => item.selected === false)  // Filter only selected items
      .map(item => item.name);

      this.transformedFilters = this.filters.map((filterItem: { function: string; value: string | string[]; operator: string }, index: number) => {
        const column = index === 0 ? "run_parameters" : `run_parameters`; 
        
        return [
          column,
          {
            operation: filterItem.function, 
            value: typeof filterItem.value === 'string' ? filterItem.value : filterItem.value.join(', '), 
          },
          filterItem.operator 
        ];
      });
      try {
        const res = await this.dataCatService.getUnSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'MANUAL',
            this.selected_path,
            this.searchSelectItems,
            this.selectedFromFilteredItems
        ).toPromise();

        console.log(res,"unselect search query!"); 

        if (res && res.body['selected_path']) {
            this.selected_path = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
      }else{
      this.transformedFilters = this.filters.map((filterItem: { function: string; value: string | string[]; operator: string }, index: number) => {
        const column = index === 0 ? "run_parameters" : `run_parameters`; 
        
        return [
          column,
          {
            operation: filterItem.function, 
            value: typeof filterItem.value === 'string' ? filterItem.value : filterItem.value.join(', '), 
          },
          filterItem.operator 
        ];
      });
      try {
        const res = await this.dataCatService.getSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'MANUAL',
            this.selected_path,
            this.searchItems,
            this.selectedFromFilteredItems
        ).toPromise();

        if (res && res.body['selected_path']) {
            this.selected_path = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
    }
      
    }else if (!this.selectedAllItems && !this.selectAllItems && this.searchItems === '' && hasEmptyValue && this.searchSelectItems == ''){ console.log("unselectred");
      this.filters = [];
      this.selectedFromFilteredItems = this.filteredItems
      .filter(item => item.selected === true)  // Filter only selected items
      .map(item => item.name);  // Extract only the 'name' property
      
      try {
        const res = await this.dataCatService.getUnSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'ALL',
            this.selected_path,
            this.searchSelectItems,
            this.selectedFromFilteredItems
        ).toPromise();

        console.log(res,"unselect query!"); 

        if (res && res.body['selected_path']) {
            this.selected_path = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
    }else if (!this.selectedAllItems && !this.selectAllItems && this.searchItems === '' && hasEmptyValue && this.searchSelectItems != ''){ console.log("unselectred search");
      this.filters = [];
      this.selectedFromFilteredItems = this.filteredItems
      .filter(item => item.selected === true)  // Filter only selected items
      .map(item => item.name);  // Extract only the 'name' property
      
      try {
        const res = await this.dataCatService.getUnSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'QUERY',
            this.selected_path,
            this.searchSelectItems,
            this.selectedFromFilteredItems
        ).toPromise();

        console.log(res,"unselect search query!"); 

        if (res && res.body['selected_path']) {
            this.selected_path = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
    }else if (this.selectedAllItems && !this.selectAllItems && this.searchItems === '' && hasEmptyValue && this.searchSelectItems !== ''){ console.log("unselectred search true value");
      this.filters = [];
      this.selectedFromFilteredItems = this.selectedFilterValues
      .filter(item => item.selected === false)  // Filter only selected items
      .map(item => item.name);  // Extract only the 'name' property
      
      try {
        const res = await this.dataCatService.getUnSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'MANUAL',
            this.selected_path,
            this.searchSelectItems,
            this.selectedFromFilteredItems
        ).toPromise();

        console.log(res,"unselect search query!"); 

        if (res && res.body['selected_path']) {
            this.selected_path = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }
    }


    this.dialogRef.close({ dataSelected: this.selected_path, dropdown: this.data.dropdown });
  }


  onClose() {
    this.dialogRef.close();
  }

  resetAdvanceSearch() {
    this.filteredItems = [...this.filteredItems];
    this.selectedPage = 1;  
    this.onUC2GenerateUniquesPagination(1);  
    this.onUC2GenerateUniquesPaginationSelected(1);  
    this.filters = [];
    this.selectAllItems = false;
    this.addNewFilter();  
  }
  


  async onUC2GenerateUniquesPagination(pageIndex: any) {
    this.showLoader = true;

    if (!pageIndex || pageIndex < 1) {
        console.error('Invalid page number:', pageIndex);
        return;
    }

    const pageDetails = {
        pageIndex: pageIndex - 1, 
        pageSize: 10, 
    };

    this.selectedFromFilteredItems = this.filteredItems
      .filter(item => item.selected === true)  // Filter only selected items
      .map(item => item.name); 

    console.log(this.selectedFromFilteredItems,"selected list");  

    if(this.selectedFromFilteredItems.length > 0){
      this.filters = [];

      try {
        const res = await this.dataCatService.getSelectQueryUniques(
            this.data.path,
            this.data.dropdown,
            pageDetails,
            this.filters,
            'MANUAL',
            this.data.selectedPath,
            this.searchSelectItems,
            this.selectedFromFilteredItems
        ).toPromise();

        console.log(res,"unselect search query!"); 

        if (res && res.body['selected_path']) {
            this.selected_path_query = res.body['selected_path'];
        }
      } catch (error) {
          this.toaster.error('Error in fetching data');
          console.error('Error in pagination fetch:', error);
      }

    }else{

    try {
      console.log(this.data.path,"selected list path");  
        // Using `this.data.selectedPath` for both `path` parameters
        const res = await this.dataCatService.getQueryUniquesAdvanced(this.data.path, this.data.dropdown, pageDetails, this.data.selectedPath).toPromise();
        console.log(res,"res get selected values")
        let uniquesItems: any[] = [];

        if (res.body['uniques']) {
            uniquesItems = res.body['uniques'].map((item: string) => ({
                name: item,
                selected: false
            }));
        }

        this.totalItems = res.body['rows_count'];
        this.totalPages = Math.max(Math.ceil(this.totalItems / this.itemsPerPage), 1);


        this.selectedItemsMap[pageIndex] = uniquesItems;
        this.filteredItems = uniquesItems;


    } catch (error) {
        this.toaster.error('Error in fetching data');
        console.error('Error in pagination fetch:', error);
    } finally {
        this.showLoader = false;
    }
  }
  }


  async onUC2GenerateUniquesPaginationSelected(pageIndex: any) {
    this.showLoader = true;

    if (!pageIndex || pageIndex < 1) {
        console.error('Invalid page number:', pageIndex);
        return;
    }

    const pageDetails = {
        pageIndex: pageIndex - 1, 
        pageSize: 10, 
    };

    try {

        const resSelected = await this.dataCatService.getQueryUniquesAdvanced(this.data.selectedPath, this.data.dropdown, pageDetails, this.data.selectedPath).toPromise();
        
        this.selectedFilterValues = []; 

        // }

        if (resSelected.body['uniques']) {
            this.selectedFilterValues = resSelected.body['uniques'].map((item: string) => ({
                name: item,
                selected: true // Mark as selected
            }));
        }


        this.totalSelectedItems = resSelected.body['rows_count'];
        this.totalSelectedItemsPages = Math.max(Math.ceil(this.totalSelectedItems / this.selectedItemsPerPage), 1);


    } catch (error) {
        this.toaster.error('Error in fetching data');
        console.error('Error in pagination fetch:', error);
    } finally {
        this.showLoader = false;
    }
  }




  filterSelectedItems() {
    const filtered = this.data.selectedList?.filter((item: { name: string; }) =>
      this.searchSelectedItems
        ? item.name.toLowerCase().includes(this.searchSelectedItems.toLowerCase())
        : true
    ) || [];
    this.paginateSelectedItems(filtered);
  }
  
  // Function to handle pagination
  onSelectedItemsPagination(page: number) {
    this.selectedItemsPage = page;
    this.paginateSelectedItems();
  }
  

  // paginateSelectedItems(filteredItems = this.data.selectedList) { 
  //   const startIndex = (this.selectedItemsPage - 1) * this.selectedItemsPerPage;
  //   const endIndex = startIndex + this.selectedItemsPerPage;

  //   this.paginatedSelectedItems = filteredItems.slice(startIndex, endIndex);
  
  //   this.transformItemsToCheckable(this.paginatedSelectedItems,this.selectedAllItems);

  //   this.totalSelectedItems = filteredItems.length;
  //   this.totalSelectedItemsPages = Math.max(Math.ceil(this.totalSelectedItems / this.selectedItemsPerPage), 1);
  // }

  paginateSelectedItems(filteredItems = this.data.selectedList || []) {
    const startIndex = (this.selectedItemsPage - 1) * this.selectedItemsPerPage;
    const endIndex = startIndex + this.selectedItemsPerPage;
  
    // Handle empty filteredItems
    this.paginatedSelectedItems = filteredItems.slice(startIndex, endIndex);
    
    this.transformItemsToCheckable(this.paginatedSelectedItems, this.selectedAllItems);
  
    // Set totals
    this.totalSelectedItems = filteredItems.length;
    this.totalSelectedItemsPages = Math.max(Math.ceil(this.totalSelectedItems / this.selectedItemsPerPage), 1);
  
    // Handle empty data case
    if (this.totalSelectedItems === 0) {
      this.paginatedSelectedItems = [];
      this.totalSelectedItemsPages = 1;
      this.selectedItemsPage = 1; // Reset to the first page
    }
  }
  

  transformItemsToCheckable(items: string[], selectedAllValue: any) {

    if(selectedAllValue == true){
      this.paginatedSelectedItems = items.map(item => ({
        name: item,
        checked: true 
    }));
    }else{
      this.paginatedSelectedItems = items.map(item => ({
          name: item,
          checked: false 
      }));
    }
  }

  onSelectedItemChange(selectedItem: any) {
    const index = this.paginatedSelectedItems.findIndex(item => item.name === selectedItem.name);
    if (index !== -1) {
        this.paginatedSelectedItems[index].checked = selectedItem.checked; 
    }
    this.selectedItemsArray = this.paginatedSelectedItems
        .filter(item => item.checked) 
        .map(item => item.name); 

    this.enableApplyButton();
  }

  

  toggleSelectedAll() {
    this.selectedAllItems = !this.selectedAllItems;
    this.selectedFilterValues.forEach(item => item.selected = this.selectedAllItems);
    this.onSelectedItemsPagination(this.selectedItemsPage);
  }


}




