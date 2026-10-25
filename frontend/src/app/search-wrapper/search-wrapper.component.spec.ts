import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { AppConfig } from '../config/app-config';
import { SearchNavigationService } from '../services/search-navigation.service';
import { SharedService } from '../services/shared.service';
import { SearchStubComponent } from '../testing/search-stub.component';

import { SearchWrapperComponent } from './search-wrapper.component';

describe('SearchWrapperComponent', () => {
  let component: SearchWrapperComponent;
  let fixture: ComponentFixture<SearchWrapperComponent>;
  let navigation: jasmine.SpyObj<SearchNavigationService>;
  const language = AppConfig.availableLangs[0];

  beforeEach(() => {
    navigation = jasmine.createSpyObj<SearchNavigationService>('SearchNavigationService', ['search']);
    navigation.search.and.returnValue(Promise.resolve(true));
    const params = { lang: language, value: 'house' };
    TestBed.configureTestingModule({
      imports: [ReactiveFormsModule, RouterTestingModule],
      declarations: [SearchWrapperComponent, SearchStubComponent],
      providers: [
        { provide: SearchNavigationService, useValue: navigation },
        { provide: ActivatedRoute, useValue: { snapshot: {
          params, paramMap: convertToParamMap(params),
          queryParams: {}, queryParamMap: convertToParamMap({}), data: { kind: 'lemma' },
        } } },
      ],
    });
    fixture = TestBed.createComponent(SearchWrapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('passes the address lookup to the child and leaves the search box empty', () => {
    const child = fixture.debugElement.query(By.directive(SearchStubComponent)).componentInstance as SearchStubComponent;
    expect(child.inputParams.lookup).toEqual({ kind: 'lemma', value: 'house' });
    expect(child.inputParams.availableLangs).toEqual([language]);
    expect(fixture.nativeElement.querySelector('input').value).toBe('');
  });

  it('submits the entered query with the selected language and clears the text box', async () => {
    const input: HTMLInputElement = fixture.nativeElement.querySelector('input');
    input.value = 'mouse';
    input.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('button[type="submit"]').click();
    await fixture.whenStable();
    expect(navigation.search).toHaveBeenCalledOnceWith('mouse', [language]);
    expect(input.value).toBe('');
  });

  it('applies menu changes to the inline results without submitting a search or clearing the draft', () => {
    const child = fixture.debugElement.query(By.directive(SearchStubComponent)).componentInstance as SearchStubComponent;
    component.searchForm.controls.searchText.setValue('draft');
    const languages = [...AppConfig.availableLangs];
    TestBed.inject(SharedService).changeAvailableLangs(languages);
    expect(child.setAvailableLangs).toHaveBeenCalledOnceWith(languages);
    expect(navigation.search).not.toHaveBeenCalled();
    expect(component.searchForm.controls.searchText.value).toBe('draft');
  });
});
