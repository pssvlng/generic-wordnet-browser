# en-word.net comparison fixture

`en-word-net-i46360.ttl` is the unchanged response downloaded on 2026-10-25
from <https://en-word.net/ttl/synset/02086723-n>.
The ILI was resolved using <https://en-word.net/api/synset_by_ili/i46360>;
`GET /synset/02086723-n` with `Accept: text/turtle` redirects to that export.

Data: English WordNet, <https://en-word.net/>, CC BY 4.0
(<https://creativecommons.org/licenses/by/4.0/>).

The regression test normalizes application-specific URIs and checks RDF graph
isomorphism, so Turtle ordering, prefixes and blank-node IDs do not matter.
The installed EWN 2020 contains one extra dog-to-pack `holoMember` relation
(four triples including its reification). The test explicitly verifies and
excludes that data difference when comparing with the reference graph.
Tests use this snapshot and do not access the network.

`en-word-net-i46360.xml` is the unchanged response from
<https://en-word.net/xml/synset/02086723-n>, downloaded on 2026-10-25.
It uses WN-LMF 1.4. The XML tests compare its core lookup structure and data,
allowing for native IDs and source-release differences.

`WN-LMF-1.4.dtd` is the unmodified official schema downloaded on the same date
from <https://globalwordnet.github.io/schemas/WN-LMF-1.4.dtd>.
XML subset validation permits unresolved **relation target** references only,
as in en-word.net's lookup response. All other DTD errors fail the test;
entry members, sense-to-synset links and frame references must resolve locally.
