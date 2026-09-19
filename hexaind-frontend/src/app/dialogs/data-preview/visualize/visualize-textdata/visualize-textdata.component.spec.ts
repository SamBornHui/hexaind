import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizeTextdataComponent } from './visualize-textdata.component';

describe('VisualizeTextdataComponent', () => {
  let component: VisualizeTextdataComponent;
  let fixture: ComponentFixture<VisualizeTextdataComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [VisualizeTextdataComponent]
    });
    fixture = TestBed.createComponent(VisualizeTextdataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
