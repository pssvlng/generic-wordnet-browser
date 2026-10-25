import { APP_BASE_HREF } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AppConfig } from '../config/app-config';

import { TranslationService } from './translation.service';

describe('TranslationService', () => {
  let service: TranslationService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [{ provide: APP_BASE_HREF, useValue: '/wordnet/' }],
    });
    service = TestBed.inject(TranslationService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('loads configured languages under the deployment prefix and uses their translations', () => {
    const loaded = jasmine.createSpy('loaded');
    service.preloadTranslations().subscribe(loaded);
    for (const lang of AppConfig.availableLangs) {
      const request = http.expectOne(`/wordnet/assets/i18n/${lang}.json`);
      expect(request.request.method).toBe('GET');
      request.flush({ greeting: `Hello in ${lang}` });
    }
    expect(loaded).toHaveBeenCalledTimes(1);
    for (const lang of AppConfig.availableLangs) {
      expect(service.translate('greeting', lang)).toBe(`Hello in ${lang}`);
    }
  });
});
