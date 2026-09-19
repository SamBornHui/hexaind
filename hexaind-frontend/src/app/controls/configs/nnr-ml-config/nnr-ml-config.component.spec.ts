import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NnrMlConfigComponent } from './nnr-ml-config.component';

describe('NnrMlConfigComponent', () => {
  let component: NnrMlConfigComponent;
  let fixture: ComponentFixture<NnrMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [NnrMlConfigComponent]
    });
    fixture = TestBed.createComponent(NnrMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
