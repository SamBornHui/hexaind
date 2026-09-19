import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UpdateDatasetsComponent } from './update-datasets.component';

describe('CreateNewProjectComponent', () => {
  let component: UpdateDatasetsComponent;
  let fixture: ComponentFixture<UpdateDatasetsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UpdateDatasetsComponent]
    });
    fixture = TestBed.createComponent(UpdateDatasetsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
