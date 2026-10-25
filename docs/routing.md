# Lookup URLs

The address records the lookup explicitly opened in the browser or submitted
through the search box. Refreshing or using browser back/forward reproduces
that lookup. Browsing results inside the page uses a separate local history.

| Shortcut | Canonical browser URL | Results |
| --- | --- | --- |
| `/lemma/mouse` | `/view/lemma/mouse` | Matches in all configured languages |
| `/en/lemma/mouse` | `/view/en/lemma/mouse` | English matches only |
| `/ili/i46593` | `/view/ili/i46593` | The concept in all configured languages |
| `/de/ili/i46593` | `/view/de/ili/i46593` | The concept in German only |
| `/synset/ewn-02124272-n` | `/view/synset/ewn-02124272-n` | Exactly this English synset |
| `/en/synset/ewn-02124272-n` | `/view/en/synset/ewn-02124272-n` | The same English synset |
| `/de/synset/ewn-02124272-n` | `/view/de/synset/ewn-02124272-n` | No match: this ID belongs to English |
| `/id/ewn-02124272-n` | `/view/synset/ewn-02124272-n` | Alias for a synset lookup |

All three lookup types and the `id` alias accept the optional language prefix.
Canonical URLs always put `view` first, followed by the optional language.
Resource URLs perform HTTP content negotiation before the application loads.
Angular also understands shortcuts pasted into the search box.

## Content negotiation

The resource URI identifies the lookup. A `GET` or `HEAD` request receives
`303 See Other` to the representation selected by the `Accept` header:

| Accept | Location for `/en/lemma/dog` | Representation |
| --- | --- | --- |
| `text/html` | `/view/en/lemma/dog` | Browser interface |
| `application/json` | `/api/en/lemma/dog` | Structured lookup document |
| `text/turtle` | `/ttl/en/lemma/dog` | OntoLex/WordNet RDF in Turtle |
| `application/rdf+xml` | `/rdf/en/lemma/dog` | The same RDF graph in RDF/XML |
| `application/xml` | `/xml/en/lemma/dog` | WN-LMF 1.4 XML lookup subset |

This applies equally to `lemma`, `synset`, `ili` and the `id` alias, with or
without a language prefix. Explicit representation URLs can be requested
directly. `/view/...` always serves the application; request the resource URI
or a data representation URI for data.

```bash
# Inspect negotiation without following the redirect:
curl -I -H 'Accept: text/turtle' http://localhost:4200/en/lemma/dog

# Follow the redirect and retrieve the data:
curl -L -H 'Accept: application/json' http://localhost:4200/en/lemma/dog
curl -L -H 'Accept: text/turtle' http://localhost:4200/de/ili/i46593
curl -L -H 'Accept: application/rdf+xml' http://localhost:4200/ili/i46593
curl -L -H 'Accept: application/xml' http://localhost:4200/en/ili/i46360
```

No `Accept` header or `*/*` defaults to HTML. Media ranges, quality weights and
`q=0` exclusions are respected; equal preferences use HTML, JSON, Turtle,
RDF/XML, then WN-LMF XML. Unsupported requested media types return `406 Not Acceptable`.
`application/xml` selects WN-LMF; `application/rdf+xml` selects RDF/XML.
The explicit `/xml/...` and `/rdf/...` representations enforce this distinction.

Negotiation responses include `Vary: Accept` and can be cached for five minutes.
Data responses include their media type, `Content-Location`, alternate-format
`Link` headers and a weak ETag. Clients must revalidate cached data;
`If-None-Match` supports `304 Not Modified`. `HEAD` returns the corresponding
headers without a body. Invalid queries return `400`, missing data `404`, and
known data-backend failures `503`, with JSON errors and `Cache-Control: no-store`.
HTML lookups still reach the view so it can display invalid-query or no-results
messages. Data endpoints reject conflicting, unknown and repeated parameters.

JSON has `schemaVersion: 1`, `query`, `count` and `synsets`. It preserves native
lexicon and synset identifiers, languages, ILIs, lemmas, definitions, examples,
lexical entries, senses and stored semantic/lexical relation links. RDF uses
[OntoLex-Lemon](https://www.w3.org/2016/05/ontolex/) and the
[Global WordNet vocabulary](https://globalwordnet.github.io/schemas/wn), with
language-tagged text and links to the ILI. Both serializations come from the
same graph. Source versions and licences in JSON come from the installed lexicons.
These are lookup exports, not full-database downloads.
Relations link to other resources without recursively exporting them.

RDF lookup exports follow [en-word.net's subset serializer](https://github.com/jmccrae/ewe/blob/main/ewe_lib/src/wordnet/rdf/writer.rs):
canonical forms, lexical entries and senses, `skos:inScheme`, `wn:lexfile` when
stored, definition/example blank nodes containing `rdf:value`, camelCase
WordNet relation predicates, and accompanying `vartrans` relation nodes.
Sense relation nodes have type `ontolex:SenseRelation`; concept relation nodes
have no extra type. Like en-word.net's lookup exports, these omit the
whole-lexicon metadata header. JSON retains the source metadata.
Frame declarations include each returned lexicon's complete stored table;
`synsem:synBehavior` links entries to the frames of their returned senses.
Language tags and frame URIs remain scoped to the source language/lexicon.
Older datasets without frame IDs use stable hashes of the stored labels.
The frame-table adapter uses the pinned `wn==0.9.4` database schema; review it
when upgrading wn. This runs only for exports and does not affect UI searches.

The English `i46360` graph is checked against a saved live en-word.net response.
After URI normalization it matches, except for one additional dog-to-pack
relation in the installed EWN 2020. Differences between lexicon releases are
preserved, rather than changing source facts to match another release.
en-word.net's live ILI URL does not itself negotiate RDF: resolve its ILI via
`/api/synset_by_ili/i46360`, then negotiate `/synset/02086723-n`.
This application's `/en/ili/i46360` negotiates directly.

WN-LMF XML uses the [1.4 schema](https://globalwordnet.github.io/schemas/),
as does en-word.net's live `/xml/...` export. A single `LexicalResource`
contains one `Lexicon` per returned source lexicon, with its native metadata,
language, version and licence. Entries are deduplicated across selected
synsets. Their forms, pronunciations, tags, selected senses, original sense
order/ranks, examples, counts and stored relations are retained. Synsets
include their native IDs, ILIs, definitions, member IDs, examples and stored
relations. Sense `subcat` references resolve to lexicon-scoped frame declarations.
Optional values are emitted only when stored; no foreign source metadata is
invented. The selective XML adapter also uses the pinned wn 0.9.4 internals.

Like en-word.net's per-lookup XML, these are **subsets**: relation targets may
refer to senses/synsets outside the response. They are not self-contained
wordnet installation files and therefore do not meet the full DTD's requirement
that every relation target be declared locally. Tests validate against a saved
official DTD, permitting only those unresolved relation targets; all other
structure and references must validate. We retain known native sense targets
even outside the subset, where en-word.net sometimes omits them when its
lookup serializer cannot reconstruct the target sense ID.
XML ETags hash the serialized XML, including data not present in the JSON
lookup schema. XML export does not perform any remote requests or expand the
entire lexicon, and does not change UI lookup behaviour.

## Language selection

With no filter, the frontend passes all languages in `AppConfig.availableLangs`;
data exports use the backend's `WORDNET_LANGUAGES` allowlist. Keep these aligned.
A single language selection uses a prefix. A subset containing multiple
languages uses, for example, `/view/lemma/chat?langs=de,fr`. Loading an address
updates the menu. Menu changes update results in-page without changing the
address; the next submitted search records the current selection in its URL.
Unknown languages and conflicting prefix/query
filters show an error instead of silently searching a different language.

ILI links stay ILI links: they do not redirect to an arbitrarily chosen
language's synset. An ILI lookup returns that concept's equivalents in the
selected languages. If no equivalent exists, that language contributes no result.

A synset ID identifies one synset in a particular lexicon and language. A
synset lookup returns only that entry, even with all languages selected; it
never expands through its ILI. A language prefix or `langs` filter can exclude
the entry, but cannot translate it. A conflicting filter shows no results in
the browser (the browser lookup API returns `[]`) and returns `404` from the
JSON/Turtle/RDF export endpoints. The `id` alias follows the same rules.
Explicit relation queries on a synset follow that entry's relations without
expanding the targets through their ILIs, and validate the source language first.

For example, `ewn-02086723-n` is the English dog synset. `/view/synset/ewn-02086723-n`
and `/view/en/synset/ewn-02086723-n` both return that one synset;
`/view/de/synset/ewn-02086723-n` has no match. Use `/view/ili/i46360` for its
configured language equivalents, or `/view/de/ili/i46360` for German only.

## Search input and identifiers

Lemma searches first collect direct matches across every selected language.
Only when that whole search has no matches do they try language-specific
lemmatization (for example, `spouses` → `spouse`). This avoids running language
models for six unmatched languages when a word already matches English.
Language filters apply to both passes.

Each backend worker loads the configured languages' lemmatizers during startup
and reuses them across requests. Initialization and shared-pipeline inference
are protected for concurrent requests. This moves the model-loading cost to
startup; model changes require a worker restart. If an optional model is
missing, the worker logs it once and retains direct WordNet searches for that
language, without lemmatization fallback. No models are downloaded on requests.

The search box recognizes ordinary words, `i46593`-style ILIs, native synset
identifiers such as `ewn-02124272-n`, and the application's existing word keys
such as `cat.n.02124272.ewn`. It also accepts lookup paths and pasted lookup
URLs. Use `lemma:i46593` to force a literal lemma search when a word resembles
an identifier; `ili:…` and `synset:…` are also supported.

Bare synset offsets such as `02124272-n` resolve against installed English
lexicons, which serve as the multilingual pivot. If more than one lexicon
matches, the API asks for a qualified identifier. A supplied lexicon prefix
is never removed or replaced: offsets can differ across WordNet releases, so
an `oewn-…` identifier cannot safely be treated as an `ewn-…` identifier.

The examples above use the locally installed English WordNet 2020. Use an ILI
when sharing a concept across languages or lexicons. URL values are encoded
as single segments, including spaces, Unicode, ampersands, slashes and hashes.

Inline synonyms, translations, semantic relations and related-word details
keep the current address and search field unchanged. The in-page back arrow
restores earlier results, their title and page. Submitting a new search resets
this local history, including when it submits the same lookup URL again.
The search field clears after submission, as in the original interface;
navigation does not populate it with synset identifiers or ILIs.

Explicit URLs can still include `?relation=hypernym` (also hyponym, holonym,
meronym, antonym and entailment). `?word=…` retains a selected
synonym/translation as the displayed word. These parameters are accepted on
incoming URLs, but inline clicks do not generate new URLs. Refreshing during
inline browsing returns to the last explicitly submitted lookup. The existing
image route and old `#/search-wrapper` bookmarks remain supported.

## API and deployment

`GET /api/dict/lookup/{lemma|synset|ili}/{value}` returns the existing browser
word DTOs. `filterlang=en,de,…` selects the languages and `lang=de` optionally
restricts results to one of them. `relation=…` requests related concepts.
Invalid queries return a JSON error; valid queries without matches return `[]`.
The older `/api/dict/words/` endpoint is still available for existing clients.

Angular uses path routing. The development proxy and `frontend/nginx.conf`
send resource and data representation URLs to Flask; `/view/...` and other SPA
deep links fall back to `index.html`. Consequently, both data and browser URLs
use the same public origin. Nginx sends each deployment to its paired backend,
which is particularly important when several language editions share a host.

The frontend Docker build takes `BASE_HREF` (default `/`) and `BACKEND_UPSTREAM`
(default `backend:5000`). The language-specific Compose files set these to their
existing mount point and paired backend. Configure the backend as follows:

| Setting | Example | Purpose |
| --- | --- | --- |
| `WORDNET_LANGUAGES` | `en,de,fr` | Allowed lookup/export languages; use the same set as the frontend |
| `WORDNET_URL_PREFIX` | `/wordnet` | Public mount path stripped by Traefik; empty for a root deployment |
| `WORDNET_PUBLIC_URL` | `https://example.org/wordnet` | Stable public base for RDF/JSON resource identifiers |

Set `WORDNET_PUBLIC_URL` explicitly in production, including the HTTPS scheme
and mount path. The Compose variants read `WORDNET_PUBLIC_URL_EU`,
`WORDNET_PUBLIC_URL_EN`, `WORDNET_PUBLIC_URL_DE`, etc.; the root Compose file
reads `WORDNET_PUBLIC_URL`. Its path must match `WORDNET_URL_PREFIX` or startup
fails. Without it, local development derives identifiers from the request
origin. Forwarded host/protocol/prefix headers are deliberately not used to
construct canonical identifiers.

For example, the EU edition uses frontend `BASE_HREF=/wordnet/`, backend
`WORDNET_URL_PREFIX=/wordnet`, and `WORDNET_PUBLIC_URL_EU=https://example.org/wordnet`.
Keep these values aligned with Traefik's stripped prefix. A request to
`/wordnet/en/lemma/dog` then redirects to `/wordnet/view/en/lemma/dog` or the
corresponding data URL. Translation assets use the configured base too.
Existing deployments need frontend and backend rebuilds for these changes.

## Verification

With backend and frontend development servers running:

```bash
cd backend
python3 -m pip install -r requirements-test.txt
python3 -m unittest discover -s tests -v
cd ../frontend
npx playwright install chromium
npm run test:e2e
```

`CHROME_BIN` can select an existing Chromium executable; `E2E_BASE_URL` can
select another development-server origin. Routing tests use controlled API
responses plus live English/German ILI checks against the configured local data.
HTTP tests also verify redirects with JavaScript disabled. Backend tests cover
quality weights, language constraints, RDF graph equivalence, WN-LMF schema
structure, native identities, multilingual grouping, forms, sense/frame links,
source metadata, escaping, conditional requests and deployment prefixes.

## Reference investigation

The [en-word.net implementation](https://github.com/jmccrae/ewe/blob/main/ewe_dioxus/README.md#routes)
defines lemma and synset browser pages, content-negotiated `/lemma/…` and
`/synset/…` entry points, and identifier-aware search. Its
[identifier redirects](https://github.com/jmccrae/ewe/blob/main/ewe_dioxus/src/backend/rdf.rs)
also support `/id/…`. Its [ILI page](https://github.com/jmccrae/ewe/blob/main/ewe_dioxus/src/views/by_ili.rs)
resolves an ILI to a single English synset. We keep the ILI address to support
multilingual results.

The site's `/view/senses/…` corpus concordances, full-dataset downloads
and editing history are separate features and are outside this change's scope.
