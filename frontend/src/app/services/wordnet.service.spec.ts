import { TestBed } from '@angular/core/testing';

import { WordnetService } from './wordnet.service';

describe('WordnetService', () => {
  let service: WordnetService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WordnetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
