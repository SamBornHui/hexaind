import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataStructureComponent } from './data-structure.component';

describe('DataComponent', () => {
  let component: DataStructureComponent;
  let fixture: ComponentFixture<DataStructureComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DataStructureComponent]
    });
    fixture = TestBed.createComponent(DataStructureComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
