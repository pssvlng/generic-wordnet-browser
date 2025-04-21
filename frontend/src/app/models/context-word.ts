import { BaseWord } from "./base-word";

export interface ContextWord extends BaseWord {
    lemma: string
    whitespace: string
    dbPediaUrl: string
    lang: string
}