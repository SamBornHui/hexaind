import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataCatalogComponent } from './data-catalog.component';

describe('DataCatalogComponent', () => {
  let component: DataCatalogComponent;
  let fixture: ComponentFixture<DataCatalogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DataCatalogComponent]
    });
    fixture = TestBed.createComponent(DataCatalogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
