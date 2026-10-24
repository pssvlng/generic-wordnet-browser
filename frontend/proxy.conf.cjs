// Route resource negotiation to Flask before the SPA fallback runs.
// Preserve the external Host so development RDF URIs use the frontend origin.
const language = '(?:[a-z]{2,3}(?:-[A-Za-z0-9]+)*/)?';
const resource = new RegExp('^/(?:' + language + '(?:lemma|synset|ili|id)/' +
  '|(?:api|ttl|rdf)/' + language + '(?:lemma|synset|ili|id)/)');

module.exports = [{
  context: pathname => pathname.startsWith('/api/dict/') || resource.test(pathname),
  target: 'http://127.0.0.1:5000',
  changeOrigin: false,
  logLevel: 'warn',
}];
