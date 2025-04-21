import { ContextWord } from "./context-word";

export interface RdfLiteral {
    predicate: string
    contextWords: Array<ContextWord>;
    text: string;
    lang: string;
}