import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ProblemType } from 'src/app/models/workflow-models';

@Component({
  selector: 'app-features-list-common',
  templateUrl: './features-list-common.component.html',
  styleUrls: ['./features-list-common.component.less'],
})
export class FeaturesListCommonComponent {
  isScientificNotationEnabled: boolean = false;
  numFeatureSearch: string = '';
  allInputChecked = true;
  catFeatureSearch: string = '';
  allCatInputChecked = false;
  @Input() numericalDataSource: any;
  @Input() categoricalDataSource: any;
  @Input() configCache: any;
  @Input() isMultipleOutputSelection = false
  @Output() changeMade = new EventEmitter<any>();
  searchTerm: string = '';
  numercalFeatures: any;
  categoricalFeatures: any;
  numericalTableHeight = '400px';
  catergoricalTableHeight = '400px';

  constructor(public toaster: ToastrService) { }

  ngOnInit() {
    if (this.configCache.problem_type == undefined) {
      this.configCache.problem_type = ProblemType.Regression
    }

  }
  ngOnChanges() {
    this.allInputChecked = !(this.numericalDataSource.filter((element: any) => {
      return !element.inputChecked
    }).length)
    this.allCatInputChecked = !(this.categoricalDataSource.filter((element: any) => {
      return !element.inputChecked
    }).length)
    this.numercalFeatures = this.numericalDataSource;
    this.categoricalFeatures = this.categoricalDataSource;
    this.calculateTableHeights()
  }

  calculateTableHeights() {

    const getTableHeight = (dataSourceLength : any) => {
      if (dataSourceLength >= 0 && dataSourceLength <= 2) return '130px';
      if (dataSourceLength >= 3 && dataSourceLength <= 4) return '230px';
      if (dataSourceLength >= 5 && dataSourceLength <= 6) return '330px';
      return '400px'; // Default height for lengths 6 or more
    };

    this.numericalTableHeight = getTableHeight(Object.keys(this.numericalDataSource).length);
    this.catergoricalTableHeight = getTableHeight(Object.keys(this.categoricalDataSource).length);
  }


  searchFeatureList(event: any) {
    if (this.searchTerm != '') {
      this.numericalDataSource = this.numercalFeatures.filter((element: { name: string; }) => element.name.toLowerCase().includes(this.searchTerm.toLowerCase()))
      this.categoricalDataSource = this.categoricalFeatures.filter((element: { name: string; }) => element.name.toLowerCase().includes(this.searchTerm.toLowerCase()))
    } else {
      this.numericalDataSource = this.numercalFeatures;
      this.categoricalDataSource = this.categoricalFeatures;
    }
  }

  toggleCheckbox(event: any, elementData: any, type: 'input' | 'output'): void {
    const columnName = elementData.name;
    if (this.configCache?.problem_type === ProblemType.Classification) {
      if (elementData.data_type === 'numerical' && type === 'output') {
        // If it's a numerical feature, prevent selecting it as an output
        this.toaster.info(
          'Numerical features cannot be selected as output',
          'INFO',
          { positionClass: 'custom-toast-position' },
        );
        elementData.outputChecked = false;
        return;
      }
    }

    if (type === 'input' && this.configCache) {
      if (!this.isMultipleOutputSelection || this.configCache.problem_type == ProblemType.Classification) {
        if (elementData.inputChecked) {
          if (!this.configCache.input_cols.includes(columnName)) {
            this.configCache.input_cols.push(columnName);
          }
          if (this.configCache.output_col === columnName) {
            this.configCache.output_col = ''; // Reset output_col if it matches columnName
          }
          elementData.outputChecked = false;
        } else {
          const inputIndex = this.configCache.input_cols.indexOf(columnName);
          if (inputIndex > -1) {
            this.configCache.input_cols.splice(inputIndex, 1);
          }
        }
      }
      else {
        if (elementData.inputChecked) {
          const outputIndex = this.configCache.output_cols.indexOf(columnName);
          if (outputIndex > -1) {
            this.configCache.output_cols.splice(outputIndex, 1);
            elementData.outputChecked = false;
          }

          if (!this.configCache.input_cols.includes(columnName)) {
            this.configCache.input_cols.push(columnName);
          }
        } else {
          if (this.configCache.input_cols.indexOf(columnName) != -1) {
            this.configCache.input_cols.splice(this.configCache.input_cols.indexOf(columnName), 1)
          }
        }
      }
    } else if (type === 'output' && this.configCache) {
      if (elementData.outputChecked) {
        if (!this.isMultipleOutputSelection || this.configCache.problem_type == ProblemType.Classification) {
          if (this.configCache.output_col !== columnName) {
            this.configCache.output_col = columnName;
          }
          const inputIndex = this.configCache.input_cols.indexOf(columnName);
          if (inputIndex > -1) {
            this.configCache.input_cols.splice(inputIndex, 1);
          }
          elementData.inputChecked = false;
          if (this.configCache?.problem_type === ProblemType.Regression) {
            for (var i = 0; i < this.numericalDataSource.length; i++) {
              if (this.numericalDataSource[i].name != elementData.name) {
                this.numericalDataSource[i].outputChecked = false;
              }
            }
            for (var i = 0; i < this.categoricalDataSource.length; i++) {
              this.categoricalDataSource[i].outputChecked = false;
            }
          }
          if (this.configCache?.problem_type === ProblemType.Classification) {
            for (var i = 0; i < this.numericalDataSource.length; i++) {
              this.numericalDataSource[i].outputChecked = false;
            }
            for (var i = 0; i < this.categoricalDataSource.length; i++) {
              if (this.categoricalDataSource[i].name != elementData.name) {
                this.categoricalDataSource[i].outputChecked = false;
              }
            }
          }
        } else {
          elementData.inputChecked = false;
          const inputIndex = this.configCache.input_cols.indexOf(columnName);
          if (inputIndex > -1) {
            this.configCache.input_cols.splice(inputIndex, 1);
          }
          this.configCache.output_cols.push(columnName);
        }
      } else {
        if (this.configCache.output_col && this.configCache.output_col === columnName) {
          this.configCache.output_col = '';
        } else {
          this.configCache.output_cols.splice(this.configCache.output_cols.indexOf(columnName), 1);
        }
      }
    }
    this.updateSelectAllCheckboxStatus();
    this.changeMade.emit(true)
  }

  updateSelectAllCheckboxStatus(): void {
    this.allInputChecked = this.numericalDataSource.every(
      (item: any) => item.inputChecked,
    );
    this.allCatInputChecked = this.categoricalDataSource.every(
      (item: any) => item.inputChecked,
    );
  }

  toggleAllCheckbox(event: any) {
    if (this.allInputChecked && this.configCache) {
      if (this.numFeatureSearch == '') {
        for (var i = 0; i < this.numericalDataSource.length; i++) {
          this.numericalDataSource[i].inputChecked = true;
          this.numericalDataSource[i].outputChecked = false;
          let index = this.configCache?.input_cols.findIndex((item: any) => item == this.numericalDataSource[i].name);
          if (index == -1) {
            this.configCache?.input_cols.push(this.numericalDataSource[i].name);
          }
          if (this.configCache.output_col) {
            this.configCache.output_col = '';
          } else {
            this.configCache.output_cols = []
          }
        }
      } else {
        let filtereditems = this.numericalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return item.name && item.name.toLowerCase().includes(this.numFeatureSearch.toLocaleLowerCase());
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.numericalDataSource.findIndex((item: any) => item.name == feature.name);
            this.numericalDataSource[index].inputChecked = true;
            this.numericalDataSource[index].outputChecked = false;

            let indexCol = this.configCache?.input_cols.findIndex((item: any) => item == feature.name);
            if (indexCol == -1) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (!this.configCache?.input_cols.includes(feature.name)) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (this.configCache.output_col) {
              this.configCache.output_col = '';
            } else {
              this.configCache.output_cols = []
            }
          });
        }
      }
      this.changeMade.emit(true)
    } else {
      if (this.numFeatureSearch == '') {
        for (var i = 0; i < this.numericalDataSource.length; i++) {
          this.numericalDataSource[i].inputChecked = false;
          if (this.configCache) {
            let index = this.configCache.input_cols.indexOf(this.numericalDataSource[i].name);
            if (index != -1) {
              this.configCache.input_cols.splice(index, 1);
            }
          }
        }
      } else {
        let filtereditems = this.numericalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return item.name && item.name.toLowerCase().includes(this.numFeatureSearch.toLocaleLowerCase());
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.numericalDataSource.findIndex((item: any) => item.name == feature.name);
            this.numericalDataSource[index].inputChecked = false;
            if (this.configCache) {
              let index1 = this.configCache?.input_cols.findIndex((item: any) => item == feature.name);
              if (index1 != -1) {
                this.configCache.input_cols.splice(index1, 1);
              }
            }
          });
        }
      }

      this.changeMade.emit(true)
    }
  }

  toggleAllCheckboxCategorical(event: any) {
    if (this.allCatInputChecked && this.configCache) {
      if (this.catFeatureSearch == '') {
        for (var i = 0; i < this.categoricalDataSource.length; i++) {
          this.categoricalDataSource[i].inputChecked = true;
          this.categoricalDataSource[i].outputChecked = false;
          let index = this.configCache?.input_cols.findIndex(
            (item: any) => item == this.categoricalDataSource[i].name,
          );
          if (index == -1) {
            this.configCache?.input_cols.push(
              this.categoricalDataSource[i].name,
            );
          }
        }
      } else {
        let filtereditems = this.categoricalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return (
            item.name &&
            item.name
              .toLowerCase()
              .includes(this.numFeatureSearch.toLocaleLowerCase())
          );
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.categoricalDataSource.findIndex(
              (item: any) => item.name == feature.name,
            );
            this.categoricalDataSource[index].inputChecked = true;
            this.categoricalDataSource[index].outputChecked = false;

            if (!this.configCache?.input_cols.includes(feature.name)) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (this.configCache?.output_col == feature.name) {
              this.configCache!.output_col = '';
            }
          });
        }
      }
      this.changeMade.emit(true)
    } else {
      if (this.catFeatureSearch == '') {
        for (var i = 0; i < this.categoricalDataSource.length; i++) {
          this.categoricalDataSource[i].inputChecked = false;
          if (this.configCache) {
            let index = this.configCache.input_cols.indexOf(
              this.categoricalDataSource[i].name,
            );
            if (index != -1) {
              this.configCache.input_cols.splice(index, 1);
            }
          }
        }
      } else {
        let filtereditems = this.categoricalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return (
            item.name &&
            item.name
              .toLowerCase()
              .includes(this.numFeatureSearch.toLocaleLowerCase())
          );
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.categoricalDataSource.findIndex(
              (item: any) => item.name == feature.name,
            );
            this.categoricalDataSource[index].inputChecked = false;
            if (this.configCache) {
              let index1 = this.configCache?.input_cols.findIndex(
                (item: any) => item == feature.name,
              );
              if (index1 != -1) {
                this.configCache.input_cols.splice(index1, 1);
              }
            }
          });
        }
      }

      this.changeMade.emit(true)
    }
  }
}
