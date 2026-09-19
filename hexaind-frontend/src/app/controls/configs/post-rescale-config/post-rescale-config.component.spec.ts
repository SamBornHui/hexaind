import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PostRescaleConfigComponent } from './post-rescale-config.component';

describe('PostRescaleConfigComponent', () => {
  let component: PostRescaleConfigComponent;
  let fixture: ComponentFixture<PostRescaleConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PostRescaleConfigComponent]
    });
    fixture = TestBed.createComponent(PostRescaleConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
