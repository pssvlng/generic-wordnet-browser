import { expect, test } from '@playwright/test';

test('the frontend origin negotiates resources before the SPA loads', async ({ request }) => {
  for (const [accept, format] of [
    ['text/html', 'view'], ['application/json', 'api'],
    ['text/turtle', 'ttl'], ['application/rdf+xml', 'rdf'],
  ]) {
    const response = await request.get('/en/lemma/dog', {
      headers: { Accept: accept }, maxRedirects: 0,
    });
    expect(response.status()).toBe(303);
    expect(response.headers()['location']).toBe(`/${format}/en/lemma/dog`);
    expect(response.headers()['vary']).toContain('Accept');
    if (format !== 'view') {
      const data = await request.get(response.headers()['location'], { headers: { Accept: accept } });
      expect(data.status()).toBe(200);
      expect(data.headers()['content-type']).toContain(accept);
      expect(await data.text()).not.toContain('<app-root');
    }
  }
});

test('HTML redirects work with JavaScript disabled', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL });
  const page = await context.newPage();
  await page.goto('/en/lemma/dog');
  await expect(page).toHaveURL(/\/view\/en\/lemma\/dog$/);
  await context.close();
});

test('data requests preserve languages and conditional caching through the proxy', async ({ request }) => {
  const response = await request.get('/de/ili/i46593', { headers: { Accept: 'application/json' } });
  expect(response.status()).toBe(200);
  expect(new URL(response.url()).pathname).toBe('/api/de/ili/i46593');
  const data = await response.json();
  expect(data.synsets.length).toBeGreaterThan(0);
  expect(data.synsets.every((item: { language: string }) => item.language === 'de')).toBe(true);
  const cached = await request.get('/api/de/ili/i46593', {
    headers: { Accept: 'application/json', 'If-None-Match': response.headers()['etag'] },
  });
  expect(cached.status()).toBe(304);
  const unsupported = await request.get('/lemma/dog', { headers: { Accept: 'application/pdf' } });
  expect(unsupported.status()).toBe(406);
});
