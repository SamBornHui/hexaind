import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DsgFilesComponent } from './dsg-files.component';

describe('DsgFilesComponent', () => {
  let component: DsgFilesComponent;
  let fixture: ComponentFixture<DsgFilesComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DsgFilesComponent]
    });
    fixture = TestBed.createComponent(DsgFilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
