import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CsvDataConfigComponent } from './csv-data-config.component';

describe('CsvDataConfigComponent', () => {
  let component: CsvDataConfigComponent;
  let fixture: ComponentFixture<CsvDataConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CsvDataConfigComponent]
    });
    fixture = TestBed.createComponent(CsvDataConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
