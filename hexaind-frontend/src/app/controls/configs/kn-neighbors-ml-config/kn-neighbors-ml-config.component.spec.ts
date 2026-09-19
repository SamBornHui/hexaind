import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KnNeighborsMlConfigComponent } from './kn-neighbors-ml-config.component';

describe('KnNeighborsMlConfigComponent', () => {
  let component: KnNeighborsMlConfigComponent;
  let fixture: ComponentFixture<KnNeighborsMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [KnNeighborsMlConfigComponent]
    });
    fixture = TestBed.createComponent(KnNeighborsMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
