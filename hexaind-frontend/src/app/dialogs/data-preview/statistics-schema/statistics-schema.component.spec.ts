import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StatisticsSchemaComponent } from './statistics-schema.component';

describe('StatisticsSchemaComponent', () => {
  let component: StatisticsSchemaComponent;
  let fixture: ComponentFixture<StatisticsSchemaComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [StatisticsSchemaComponent]
    });
    fixture = TestBed.createComponent(StatisticsSchemaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
