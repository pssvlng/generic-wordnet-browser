export interface ImageInputParams {
    synsetId: string | undefined,
    fileName: string | undefined,
    level: number | undefined,
    maxLeafNodes: number | undefined,
    availableLangs: string[],
    synonymCount: number | undefined,
    hierarchy: string | undefined,
    partWhole: string | undefined,   
    filterLangs: string[],
    woi: string | undefined, 
}