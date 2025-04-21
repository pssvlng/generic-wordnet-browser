import { Component, OnDestroy, ViewChild } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AppConfig } from '../config/app-config';
import { SearchComponent } from '../search/search.component';
import { SharedService } from '../services/shared.service';

@Component({
  selector: 'app-search-wrapper',
  templateUrl: './search-wrapper.component.html',
  styleUrls: ['./search-wrapper.component.css']
})
export class SearchWrapperComponent implements OnDestroy {

  @ViewChild(SearchComponent, { static: false }) searchComponent!: SearchComponent;

  searchForm = new FormGroup({
    searchText: new FormControl<string>('', Validators.required),
  });

  availableLangs: string[] = AppConfig.availableLangs;
  placeholder: string = AppConfig.searchPlaceholders.join(' | ');
  searchButtonText: string = AppConfig.searchButtonText;

  private subscription!: Subscription;

  constructor(
    private sharedService: SharedService
  ) { }

  ngOnInit(): void {
    this.subscription = this.sharedService.currentMessage.subscribe((message: string[]) => {
      this.availableLangs = message;
      if (this.searchComponent) {       
        this.searchComponent.setAvailableLangs(this.availableLangs);
      }
    });
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  onSearch(): void {
    const woi = this.searchForm.controls['searchText'].value as string;
    if (woi) {
      const paramLangs = this.availableLangs;
      this.searchComponent.setInputParams(Object.assign({ woi, availableLangs: paramLangs }));
      this.searchForm.controls['searchText'].setValue('');
    }
  }

}
