import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { filter, startWith, Subscription } from 'rxjs';
import { AppConfig } from '../config/app-config';
import { InputParams } from '../models/input-params';
import { SearchComponent } from '../search/search.component';
import { RELATIONS, SearchNavigationService } from '../services/search-navigation.service';
import { SharedService } from '../services/shared.service';

@Component({
  selector: 'app-search-wrapper',
  templateUrl: './search-wrapper.component.html',
  styleUrls: ['./search-wrapper.component.css']
})
export class SearchWrapperComponent implements OnInit, OnDestroy {
  @ViewChild(SearchComponent) searchComponent?: SearchComponent;

  searchForm = new FormGroup({ searchText: new FormControl('', Validators.required) });
  availableLangs = [...AppConfig.availableLangs];
  placeholder = AppConfig.searchPlaceholders.join(' | ');
  searchButtonText = AppConfig.searchButtonText;
  inputParams?: InputParams;
  error = '';
  private subscription = new Subscription();
  private syncingRoute = false;
  private routeReady = false;
  private routeKey = '';

  constructor(
    private sharedService: SharedService,
    private route: ActivatedRoute,
    private router: Router,
    private navigation: SearchNavigationService,
    private title: Title,
  ) {}

  ngOnInit(): void {
    this.subscription.add(this.sharedService.currentMessage.subscribe(languages => {
      this.availableLangs = [...languages];
      if (this.routeReady && !this.syncingRoute) {
        this.searchComponent?.setAvailableLangs(languages);
      }
    }));
    this.subscription.add(this.router.events.pipe(
      filter(event => event instanceof NavigationEnd), startWith(null),
    ).subscribe(() => this.readRoute()));
  }

  private readRoute(force = false): void {
    const snapshot = this.route.snapshot;
    const key = JSON.stringify([snapshot.params, snapshot.queryParams, snapshot.data]);
    if (!force && key === this.routeKey) return;
    this.routeKey = key;
    this.routeReady = true;
    this.error = '';
    this.inputParams = undefined;
    this.searchForm.controls.searchText.setValue('');
    const lang = snapshot.paramMap.get('lang');
    const filter = snapshot.queryParamMap.get('langs');
    const requested = lang ? [lang] : filter !== null ? filter.split(',').filter(Boolean) : [...AppConfig.availableLangs];
    if (snapshot.data['invalid']) {
      this.error = 'Unknown address. Use /lemma/word, /synset/id or /ili/id, optionally prefixed with a language.';
      return;
    }
    if (!requested.length || requested.some(code => !AppConfig.availableLangs.includes(code))) {
      this.error = `Unsupported language. This application supports: ${AppConfig.availableLangs.join(', ')}.`;
      return;
    }
    if (lang && filter !== null) {
      this.error = 'Choose a language prefix or a langs query filter, rather than both.';
      return;
    }
    const relation = snapshot.queryParamMap.get('relation') || undefined;
    if (relation && !RELATIONS.includes(relation)) {
      this.error = 'Unknown semantic relation.';
      return;
    }
    const languages = AppConfig.availableLangs.filter(code => requested.includes(code));
    this.syncingRoute = true;
    this.sharedService.changeAvailableLangs(languages);
    this.syncingRoute = false;
    const kind = snapshot.data['kind'];
    const value = snapshot.paramMap.get('value');
    if (!kind || !value) {
      this.searchForm.controls.searchText.setValue('');
      this.title.setTitle(AppConfig.title);
      return;
    }
    this.title.setTitle(`${value} — ${AppConfig.title}`);
    this.inputParams = {
      lookup: { kind, value },
      woi: kind === 'lemma' ? value : snapshot.queryParamMap.get('word') || undefined,
      lang: lang || undefined, availableLangs: languages, category: relation,
      lemma: undefined, pos: undefined, wordkey: undefined, ili: undefined,
    };
  }

  async onSearch(): Promise<void> {
    const text = this.searchForm.controls.searchText.value || '';
    if (!text.trim()) return;
    try {
      const navigation = this.navigation.search(text, this.availableLangs);
      this.searchForm.controls.searchText.setValue('');
      // Angular skips an unchanged URL. Resubmitting the original search
      // must still leave an inline detail view and reset its local history.
      if (!await navigation) this.readRoute(true);
    } catch {
      this.error = 'That link is not valid. Enter a word, ILI, synset identifier or lookup URL.';
    }
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
