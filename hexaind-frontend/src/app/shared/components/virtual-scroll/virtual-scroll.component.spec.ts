import { NgFor, NgIf, NgTemplateOutlet } from '@angular/common';
import { ElementRef, SimpleChanges } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EmptyComponent } from '../empty/empty.component';
import { LoaderComponent } from '../loader/loader.component';
import {
  DefaultLimit,
  VirtualScrollComponent,
} from './virtual-scroll.component';

describe('VirtualScrollComponent', () => {
  let component: VirtualScrollComponent;
  let fixture: ComponentFixture<VirtualScrollComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VirtualScrollComponent],
      imports: [NgFor, NgIf, NgTemplateOutlet, LoaderComponent, EmptyComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(VirtualScrollComponent);
    component = fixture.componentInstance;
    component.containerEl = fixture.nativeElement;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.limit).toBe(DefaultLimit);
    expect(component.items).toEqual([]);
    expect(component.visiblePages).toEqual([0]);
    expect(component.loading).toBeFalse();
  });

  it('should reset scroll', () => {
    spyOn(component.reset, 'emit');
    component.resetScroll();
    expect(component.lastScrollTop).toBe(0);
    expect(component.isScrollDown).toBeTrue();
    expect(component.isEnd).toBeFalse();
    expect(component.loading).toBeFalse();
    expect(component.pageHeights).toEqual([]);
    expect(component.topSpacerHeight).toBe(0);
    expect(component.bottomSpacerHeight).toBe(0);
    expect(component.reset.emit).toHaveBeenCalled();
  });

  it('should handle scroll', () => {
    spyOn(component, 'updatePageHeights');
    spyOn(component, 'updateVisiblePages');
    const el = fixture.nativeElement;
    component.handleScroll(el);
    expect(component.updatePageHeights).toHaveBeenCalled();
    expect(component.updateVisiblePages).toHaveBeenCalledWith(el);
  });

  it('should update page heights', () => {
    component.pages = [
      new ElementRef({ offsetHeight: 100, getAttribute: () => '0' }),
      new ElementRef({ offsetHeight: 200, getAttribute: () => '1' }),
    ] as any;
    component.updatePageHeights();
    expect(component.pageHeights).toEqual([100, 200]);
  });

  it('should update visible pages', () => {
    const el = fixture.nativeElement;
    spyOn(component, 'checkAndUpdateVisiblePages');
    component.updateVisiblePages(el);
    expect(component.checkAndUpdateVisiblePages).toHaveBeenCalled();
  });

  it('should check and update visible pages', () => {
    spyOn(component, 'updateSpacerHeight');
    component.checkAndUpdateVisiblePages([1, 2]);
    expect(component.visiblePages).toEqual([1, 2]);
    expect(component.updateSpacerHeight).toHaveBeenCalled();
  });

  it('should update spacer height', () => {
    component.pageHeights = [100, 200, 300];
    component.visiblePages = [1];
    component.updateSpacerHeight();
    expect(component.topSpacerHeight).toBe(100);
    expect(component.bottomSpacerHeight).toBe(300);
  });

  it('should handle ngOnChanges', () => {
    const changes: SimpleChanges = {
      items: {
        currentValue: [1, 2, 3],
        previousValue: [],
        firstChange: false,
        isFirstChange: () => false,
      },
    };
    spyOn(component, 'resetScroll');
    component.ngOnChanges(changes);
    expect(component.resetScroll).toHaveBeenCalled();
  });

  it('should unsubscribe on ngOnDestroy', () => {
    component.scrollSubscription = { unsubscribe: jasmine.createSpy() } as any;
    component.ngOnDestroy();
    expect(component.scrollSubscription.unsubscribe).toHaveBeenCalled();
  });
});
