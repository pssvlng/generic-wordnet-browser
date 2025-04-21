import { ContextWord } from "./context-word";
import { RdfLiteral } from "./rdf-literal";
import { RdfNonLiteral } from "./rdf-non-literal";

export interface ContextWordWrapper {
    contextWords: Array<ContextWord[]>;
    text: string;
    is_rdf: boolean;
    rdfNonLiterals: Array<RdfNonLiteral>;
    rdfLiterals: Array<RdfLiteral>;

}