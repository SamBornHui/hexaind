import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataSheetGeneratorComponent } from './data-sheet-generator.component';

describe('DataSheetGeneratorComponent', () => {
  let component: DataSheetGeneratorComponent;
  let fixture: ComponentFixture<DataSheetGeneratorComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DataSheetGeneratorComponent]
    });
    fixture = TestBed.createComponent(DataSheetGeneratorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
