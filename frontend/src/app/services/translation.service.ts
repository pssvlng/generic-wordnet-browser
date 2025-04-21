import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, Observable, of, tap } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AppConfig } from '../config/app-config';

@Injectable({
  providedIn: 'root'
})
export class TranslationService {
  private translations: { [lang: string]: any } = {};

  constructor(private http: HttpClient) { }

  public preloadTranslations(): Observable<any> {
    const languages = AppConfig.availableLangs.map((lang) => lang.trim());
    const requests = languages.map((lang) =>
      this.http.get(`/assets/i18n/${lang}.json`).pipe(
        tap((data) => {
          this.translations[lang] = data;
        }),
        catchError((error) => {
          console.error(`Error loading translations for language: ${lang}`, error);
          return of({}); 
        })
      )
    );
    return forkJoin(requests);
  }

  public translate(key: string, lang: string): string {
    return this.translations[lang]?.[key] || this.translations['en']?.[key]; 
  }
}