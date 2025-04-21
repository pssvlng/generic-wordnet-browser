import { BaseWord } from "./base-word";
import { GenericLanguageDescriptions } from "./generic-language-descriptions";
import { LinguisticCounter } from "./linguistic-counter";

type StringListDictionary = {
    [key: string]: string[];
};

export interface Word extends BaseWord {
    identifier: "Word";
    definition: string;    
    example: string;
    synonyms: string[];
    linguisticCounter: LinguisticCounter;
    genericLanguageDescriptions: GenericLanguageDescriptions;
    relatedSynsets: Word[];
    lodViews: StringListDictionary;    
}