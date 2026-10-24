import { APP_BASE_HREF } from '@angular/common';
import { Inject, Injectable } from '@angular/core';
import { Params, Router } from '@angular/router';
import { AppConfig } from '../config/app-config';

export type LookupKind = 'lemma' | 'synset' | 'ili';
export interface Lookup {
  kind: LookupKind;
  value: string;
}
export const RELATIONS = ['hypernym', 'hyponym', 'holonym', 'meronym', 'entailment', 'antonym'];

@Injectable({ providedIn: 'root' })
export class SearchNavigationService {
  constructor(private router: Router, @Inject(APP_BASE_HREF) private baseHref: string) {}

  navigate(lookup: Lookup | undefined, languages: string[], extras: Params = {}): Promise<boolean> {
    const all = AppConfig.availableLangs.every(lang => languages.includes(lang));
    const single = !all && languages.length === 1;
    const commands = lookup
      ? ['/view', ...(single ? [languages[0]] : []), lookup.kind, lookup.value]
      : ['/'];
    const queryParams: Params = { ...extras, ...(!all && !single ? { langs: languages.join(',') } : {}) };
    if (!lookup && !all) queryParams['langs'] = languages.join(',');
    return this.router.navigate(commands, { queryParams });
  }

  search(text: string, languages: string[]): Promise<boolean> {
    const value = text.trim();
    if (!value) return Promise.resolve(false);
    // Pasted links and shorthand paths use the address-bar route validation.
    // A pasted external URL is a lookup here, never an external navigation.
    if (/^https?:\/\//i.test(value)) {
      const url = new URL(value);
      return this.openPath(url.pathname + url.search);
    }
    if (value.startsWith('/') || /^(?:[a-z]{2,3}\/)?(?:view|lemma|synset|ili|id)\//i.test(value)) {
      return this.openPath(value);
    }
    const explicit = /^(lemma|synset|ili):(.+)$/i.exec(value);
    const kind: LookupKind = explicit ? explicit[1].toLowerCase() as LookupKind
      : /^i\d+$/i.test(value) ? 'ili'
      : /^(?:[\w-]+-)?\d{8}-[nvars]$/.test(value) || /\.[nvars]\.[^.]+\.[^.]+$/.test(value)
        ? 'synset' : 'lemma';
    const term = explicit ? explicit[2].trim() : value;
    return term ? this.navigate({ kind, value: kind === 'ili' ? term.toLowerCase() : term }, languages)
      : Promise.resolve(false);
  }

  private openPath(path: string): Promise<boolean> {
    if (!path.startsWith('/')) path = '/' + path;
    if (this.baseHref !== '/' && path.startsWith(this.baseHref)) {
      path = '/' + path.slice(this.baseHref.length);
    }
    return this.router.navigateByUrl(path);
  }
}
