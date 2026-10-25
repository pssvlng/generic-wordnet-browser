import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ToastrService } from 'ngx-toastr';

import { WordnetService } from './wordnet.service';

describe('WordnetService', () => {
  let service: WordnetService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [{ provide: ToastrService, useValue: {
        toastrConfig: { positionClass: '' }, error: jasmine.createSpy('error'),
      } }],
    });
    service = TestBed.inject(WordnetService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('encodes lookup terms and sends the language and relation filters', () => {
    const received = jasmine.createSpy('received');
    service.getWords({
      lookup: { kind: 'lemma', value: 'café & ice/cream' },
      availableLangs: ['en', 'de'], lang: 'de', category: 'hypernym',
      woi: undefined, pos: undefined, lemma: undefined, wordkey: undefined, ili: undefined,
    }).subscribe(received);
    const request = http.expectOne(req => req.url === '/api/dict/lookup/lemma/caf%C3%A9%20%26%20ice%2Fcream');
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('filterlang')).toBe('en,de');
    expect(request.request.params.get('lang')).toBe('de');
    expect(request.request.params.get('relation')).toBe('hypernym');
    request.flush([]);
    expect(received).toHaveBeenCalledOnceWith([]);
  });
});
