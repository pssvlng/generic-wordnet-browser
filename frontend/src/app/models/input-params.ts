import { Lookup } from '../services/search-navigation.service';

export interface InputParams {
    lookup?: Lookup,
    woi: string | undefined,
    pos: string | undefined,
    lemma: string | undefined,
    lang: string | undefined,
    availableLangs: string [],
    category: string | undefined,
    wordkey: string | undefined,
    ili: string | undefined
}
