export interface LinguisticCounter {
    [key: string]: number; 
    hypernym: number;
    hyponym: number;
    holonym: number;
    meronym: number;
    antonym: number;
    entailment: number;
  }