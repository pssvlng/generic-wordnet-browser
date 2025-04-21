import { AfterViewInit, ChangeDetectorRef, Component, Input, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { from, mergeMap, Subject, takeUntil, tap } from 'rxjs';
import { LANG_ICON_CLASS_LOOKUP } from '../constants/lang-icon-lookup';
import { ImagePopupComponent } from '../image-popup/image-popup.component';
import { ExampleSentenceResponse } from '../models/example-sentence-response';
import { InputParams } from '../models/input-params';
import { Word } from '../models/word';
import { TranslationService } from '../services/translation.service';
import { WordnetService } from '../services/wordnet.service';

interface StringDictionary {
  [key: string]: string;
}

interface DataObject {
  [key: string]: any;
}

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent implements AfterViewInit, OnDestroy, OnInit {
  @ViewChild('popup') popup!: ImagePopupComponent;

  @Input() inputParams!: InputParams;
  @Input() fromText!: string; 

  words: Word[] = [];
  paginatedWords: Word[] = [];
  currentPage: number = 1;
  itemsPerPage: number = 10;
  totalPages: number = 0;

  title!: string;
  inputHistory: Array<[Word[], string]> = new Array<[Word[], string]>();
  loading: boolean = false;
  langIconClassLookup = LANG_ICON_CLASS_LOOKUP;

  private onDestroy$: Subject<void> = new Subject<void>();

  constructor(
    private wordnetService: WordnetService,
    private cd: ChangeDetectorRef,
    private translationService: TranslationService
  ) { }

  // Lifecycle Hooks
  ngOnInit(): void {
   
  }

  ngAfterViewInit(): void {
    if (this.inputParams) {
      this.refreshView();
    }
  }

  ngOnDestroy(): void {
    this.onDestroy$.next();
    this.onDestroy$.complete();
  }

  // Centralized Error Management
  private handleError(error: any, context: string): void {
    console.error(`Error in ${context}:`, error);
    // Optionally, add logic to display a user-friendly error message or notification.
  }

  // Utility Methods
  private getMostFrequentValue<T extends DataObject>(arr: T[], property: keyof T): T[keyof T] | null {
    const frequencyMap = new Map<T[keyof T], number>();

    arr.forEach(obj => {
      const value = obj[property];
      if (value !== undefined) {
        frequencyMap.set(value, (frequencyMap.get(value) || 0) + 1);
      }
    });

    let mostFrequentValue: T[keyof T] | null = null;
    let maxCount = 0;

    frequencyMap.forEach((count, value) => {
      if (count > maxCount) {
        maxCount = count;
        mostFrequentValue = value;
      }
    });

    return mostFrequentValue;
  }

  private processResults(results: Word[], withSenseExamples: boolean = true): void {
    const filteredResults = withSenseExamples ? results.filter(result => result.lang == "en") : [];
    const observer = {
      next: (result: ExampleSentenceResponse) => {
        if (!this.loading) { this.loading = true; }
        if (result) {
          const word = results.find(x => x.wordKey == result.word_key && x.lang == result.lang);
          if (word) {
            word.example = result.sentence;
          }
        }
      },
      error: (err: any) => this.handleError(err, 'processResults'),
      complete: () => {
        this.loading = false;
        results.forEach(item => item.definition ||= item.synonyms.join(', '));
        this.words = results;
        this.currentPage = 1;
        this.totalPages = Math.ceil(this.words.length / this.itemsPerPage);
        this.updatePaginatedWords();
      }
    };

    from(filteredResults).pipe(
      mergeMap(item =>
        this.wordnetService.getSenseExampleSentence(item.wordKey, item.name, "en").pipe(
          tap(result => console.log(`Result for ID ${item}:`, result))
        )
      ),
      takeUntil(this.onDestroy$)
    ).subscribe(observer);
  }

  private search(): void {
    this.words = [];
    this.loading = true;

    this.wordnetService.getWords(this.inputParams)
      .pipe(takeUntil(this.onDestroy$))
      .subscribe({
        next: (results: Word[]) => {
          this.processResults(results);
        },
        error: (err: any) => this.handleError(err, 'search'),
        complete: () => this.loading = false
      });
  }

  // View Management
  refreshView(): void {
    this.title = this.inputParams.lemma
      ? `${this.inputParams.lemma}(${this.inputParams.pos})`
      : this.inputParams.woi || '';

    this.search();
  }

  setInputParams(inputParams: InputParams): void {
    this.inputParams = inputParams;
    this.inputHistory = [];
    this.refreshView();
  }

  setResults(results: Word[], title: string, inputParams: InputParams | null): void {
    this.inputHistory = [];
    this.title = title;        
    this.inputParams = inputParams || this.inputParams;
    this.processResults(results);    
  }

  setAvailableLangs(langs: string[]): void {
    if (this.inputParams) {
      this.inputHistory.push([this.words, this.title]);
      this.inputParams.availableLangs = langs;
      if (this.inputParams.category !== 'synonym') {
        this.search();
      }      
    }            
  }
    
  back(): void {
    if (this.inputHistory.length > 0) {
      const p = this.inputHistory.pop() as [Word[], string];
      this.title = p[1];
      this.processResults(p[0], false);
    }
  }

  // Word Operations
  getRelatedWords(word: Word): void {
    if (word.relatedSynsets.length == 0) {
      const serviceInputParams = Object.assign({ ili: word.ili, lang: word.lang, availableLangs: this.inputParams.availableLangs, wordkey: word.wordKey });
      this.wordnetService.getRelated(serviceInputParams)
        .pipe(takeUntil(this.onDestroy$))
        .subscribe({
          next: (results: Word[]) => {
            word.relatedSynsets = results;
          },
          error: (err: any) => this.handleError(err, 'getRelatedWords'),
          complete: () => { ; }
        });
    }
  }

  displayRelatedWords(from_word: Word, words: Word[]): void {
    this.inputHistory.push([this.words, this.title]);
    this.title = `${this.getWordLangTranslation('SEARCH.SIMILAR_TO', from_word.lang)}: ${from_word.name} (${this.getWordLangTranslation('SEARCH.' + from_word.pos.toUpperCase(), from_word.lang)})`;
    this.words = [];
    words.forEach(item => item.relatedSynsets = []);
    this.processResults(words);
  }

  getWords(word: Word, category: string, woi: (string | null) = null): void {
    this.inputHistory.push([this.words, this.title]);
    this.title = `${this.getWordLangTranslation('SEARCH.' + category.toUpperCase(), word.lang)}: ${word.name} (${this.getWordLangTranslation('SEARCH.' + word.pos.toUpperCase(), word.lang)})`;
    this.inputParams = Object.assign({ wordkey: word.wordKey, lang: word.lang, availableLangs: this.inputParams.availableLangs, category: category });
    if (category == 'synonym') {
      const newWord = structuredClone(word) as Word;
      newWord.synonyms.push(newWord.name);
      newWord.synonyms = newWord.synonyms.filter(item => item !== woi);
      newWord.name = woi as string;
      this.processResults([newWord]);
    } else {
      this.search();
    }
  }

  getWordLangTranslation(key: string, lang: string): string {
    return this.translationService.translate(key, lang);
  }

  getTranslation(word: Word, lang: string, woi: string): void {
    this.inputHistory.push([this.words, this.title]);
    this.title = `${this.getWordLangTranslation('SEARCH.TRANSLATION', lang)}: ${word.name} (${this.getWordLangTranslation('SEARCH.' + word.pos.toUpperCase(), word.lang)})`;
    this.inputParams = Object.assign({ ili: word.ili, lang: lang, woi: woi, availableLangs: this.inputParams.availableLangs });
    this.search();    
  }

  // Language and Example Operations
  getOtherLangs(word: Word): string[] {
    return (this.inputParams.availableLangs)
      .filter(lang => lang !==
        word.lang && word.genericLanguageDescriptions.descriptionLookup[lang].split(',')
          .filter(item => item).length > 0);
  }

  getLangItems(word: Word, lang: string): string[] {
    return word.genericLanguageDescriptions.descriptionLookup[lang].split(',');
  }

  onGetExamples(word: Word): void {
    this.loading = true;
    this.wordnetService.getExampleSentences(word.wordKey)
      .pipe(takeUntil(this.onDestroy$))
      .subscribe({
        next: (examples: string[]) => {
          console.log(examples);
        },
        error: (err: any) => this.handleError(err, 'onGetExamples'),
        complete: () => this.loading = false
      });
  }

  hasNounOrVerb(words: Word[]): boolean {
    return words.some(x => x.pos === "Noun" || x.pos === "Verb");
  }

  hasLodViews(word: Word): boolean {
    return Object.keys(word.lodViews).length > 0;
  }

  openLodViews(lodViews: string[]): void {
    lodViews.forEach(url => {
      window.open(url, '_blank');
    });
  }

  showImage(words: Word[], woi: string | undefined = undefined): void {
    const filteredWords = words.filter(x => x.pos === "Noun" || x.pos === "Verb");

    if (filteredWords.length > 0) {
      const result = {
        fileName: "",
        synsetId: filteredWords.map(x => {
          const id = x.wordKey.split('.').reverse();
          id.pop();
          return id.join('-');
        }).join(','),
        maxLeafNodes: 5,
        synonymCount: 1,
        level: 2,
        availableLangs: this.inputParams.availableLangs,
        filterLangs: [this.getMostFrequentValue(filteredWords, 'lang') as string],
        hierarchy: "True",
        partWhole: "True",
        woi: woi,
      };
      result.fileName = `hierarchy_partwhole${Date.now()}_${[result.filterLangs[0]].join('_')}_${result.level}_${result.maxLeafNodes}_${result.synonymCount}`;
      this.popup.open(result);
    }
  }

  playAudio(text: string, lang: string): void {
    this.wordnetService.getAudio(text, lang).subscribe({
      next: (audioBlob: Blob) => {
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
      },
      error: (err: any) => {
        console.error('Error playing audio:', err);
      }
    });
  }

  updatePaginatedWords(): void {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    this.paginatedWords = this.words.slice(startIndex, endIndex);
  }

  getPageNumbers(): number[] {
    const totalPages = Math.ceil(this.words.length / this.itemsPerPage);
    const pageNumbers: number[] = [];
    for (let i = 1; i <= totalPages; i++) {
      pageNumbers.push(i);
    }
    return pageNumbers;
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updatePaginatedWords();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updatePaginatedWords();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.updatePaginatedWords();
    }
  }

}