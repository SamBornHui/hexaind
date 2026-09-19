import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DownloadRescaleVisualizeDataComponent } from './download-rescale-vizualize-data.component';

describe('DownloadRescaleVisualizeDataComponent', () => {
  let component: DownloadRescaleVisualizeDataComponent;
  let fixture: ComponentFixture<DownloadRescaleVisualizeDataComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DownloadRescaleVisualizeDataComponent]
    });
    fixture = TestBed.createComponent(DownloadRescaleVisualizeDataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
