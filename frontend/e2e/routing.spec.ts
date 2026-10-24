import { expect, test, Page } from '@playwright/test';

const pageErrors = new WeakMap<Page, string[]>();
test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  pageErrors.set(page, errors);
  page.on('pageerror', error => errors.push(error.message));
});
test.afterEach(async ({ page }) => {
  expect(pageErrors.get(page)).toEqual([]);
});

// Use deterministic responses for routing tests. Live OMW lookups are covered
// separately below and in backend/tests/test_wordnet_service.py.
const word = (lang: string, name: string) => ({
  name, lang, pos: 'Noun', offset: '02124272', wordKey: 'cat.n.02124272.ewn',
  wordnetId: 'own', ili: 'i46593', definition: `Definition of ${name}`,
  example: '', synonyms: ['synonym'], linguisticCounter: { hypernym: 1 },
  genericLanguageDescriptions: { descriptionLookup: { en: '', de: 'Katze', fr: 'chat' } },
  lodViews: {}, relatedSynsets: [],
});

async function mockLookups(page: Page) {
  await page.route('https://edu.yovisto.com/**', route => route.fulfill({ json: { results: { bindings: [] } } }));
  await page.route('**/api/dict/lookup/**', route => {
    const url = new URL(route.request().url());
    const name = decodeURIComponent(url.pathname.split('/').pop()!);
    const languages = url.searchParams.get('lang')?.split(',') || url.searchParams.get('filterlang')!.split(',');
    return route.fulfill({ json: languages.map(lang => word(lang, name)) });
  });
  await page.route('**/api/dict/words/**', route => {
    const query = new URL(route.request().url()).searchParams;
    return route.fulfill({ json: [word(query.get('lang') || 'en', query.get('category') || query.get('woi') || 'result')] });
  });
  await page.route('**/api/dict/related/**', route => route.fulfill({ json: [word('en', 'related word')] }));
}

test('shortcut and canonical URLs load and survive refresh', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await mockLookups(page);
  await page.goto('/lemma/mouse');
  await expect(page).toHaveURL(/\/view\/lemma\/mouse$/);
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await page.reload();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await expect(page.getByRole('textbox')).toHaveValue('');
  await expect(page).toHaveTitle(/mouse/);
  expect(errors).toEqual([]);
});

test('language prefixes, ILI and id aliases work', async ({ page }) => {
  await mockLookups(page);
  for (const [shortcut, canonical] of [
    ['/en/lemma/mouse', '/view/en/lemma/mouse'],
    ['/de/ili/i46593', '/view/de/ili/i46593'],
    ['/id/ewn-02124272-n', '/view/synset/ewn-02124272-n'],
    ['/en/id/02124272-n', '/view/en/synset/02124272-n'],
    ['/synset/cat.n.02124272.ewn', '/view/synset/cat.n.02124272.ewn'],
  ]) {
    await page.goto(shortcut);
    await expect(page).toHaveURL(new RegExp(canonical.replace(/\./g, '\\.') + '$'));
    await expect(page.locator('mat-expansion-panel').first()).toBeVisible();
    await expect(page.getByRole('textbox')).toHaveValue('');
  }
});

test('search recognizes words and identifiers and browser history restores state', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/');
  for (const [input, path] of [
    ['mouse', '/view/lemma/mouse'], ['i46593', '/view/ili/i46593'],
    ['ewn-02124272-n', '/view/synset/ewn-02124272-n'],
    ['de/lemma/Maus', '/view/de/lemma/Maus'],
  ]) {
    await page.getByRole('textbox').fill(input);
    await page.getByRole('button', { name: 'Search', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(path + '$'));
    await expect(page.getByRole('textbox')).toHaveValue('');
  }
  await page.goBack();
  await expect(page).toHaveURL(/\/view\/synset\/ewn-02124272-n$/);
  await expect(page.getByRole('textbox')).toHaveValue('');
  await expect(page.locator('mat-panel-title').first()).toContainText('ewn-02124272-n');
  await page.goForward();
  await expect(page.getByRole('textbox')).toHaveValue('');
  await expect(page.locator('mat-panel-title').first()).toContainText('Maus');
});

test('language changes stay inline and apply to the next submitted search URL', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/view/de/lemma/Maus');
  await page.locator('.menu-button').click();
  await expect(page.getByRole('checkbox', { name: 'German', exact: true })).toBeChecked();
  await expect(page.getByRole('checkbox', { name: 'English', exact: true })).not.toBeChecked();
  await page.getByRole('checkbox', { name: 'French', exact: true }).check();
  await expect(page).toHaveURL(/\/view\/de\/lemma\/Maus$/);
  await expect(page.locator('.search-results > mat-accordion > mat-expansion-panel')).toHaveCount(2);
  await page.getByRole('textbox').fill('chat');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page).toHaveURL(/\/view\/lemma\/chat\?langs=de,fr$/);
  await page.reload();
  await expect(page.locator('mat-panel-title')).toHaveCount(4); // two result and two related panels
  await expect(page.getByRole('button', { name: 'Back to previous results' })).toHaveCount(0);
});

test('reserved characters are encoded as one lemma and reach the API intact', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/');
  const lemma = 'café & ice/cream?#%;';
  await page.getByRole('textbox').fill(lemma);
  const request = page.waitForRequest(req => req.url().includes('/api/dict/lookup/lemma/'));
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  expect(decodeURIComponent(new URL((await request).url()).pathname.split('/lookup/lemma/')[1])).toBe(lemma);
  await page.reload();
  await expect(page.locator('mat-panel-title').first()).toContainText(lemma);
  await expect(page.getByRole('textbox')).toHaveValue('');
});

test('unsupported routes and languages show an error instead of a different search', async ({ page }) => {
  await mockLookups(page);
  for (const path of ['/xx/lemma/mouse', '/view/ili/i46593?langs=xx', '/view/en/lemma/mouse?langs=de', '/unknown/path']) {
    await page.goto(path);
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.locator('app-search')).toHaveCount(0);
  }
});

test('a slower previous search cannot replace the latest results', async ({ page }) => {
  await mockLookups(page);
  await page.route('**/api/dict/lookup/lemma/slow*', async route => {
    await new Promise(resolve => setTimeout(resolve, 600));
    await route.fulfill({ json: [word('en', 'slow')] });
  });
  await page.goto('/view/lemma/slow');
  await page.getByRole('textbox').fill('fast');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('fast');
  await page.waitForTimeout(800);
  await expect(page.locator('mat-panel-title').first()).toContainText('fast');
});

test('live ILI lookup returns all configured languages, with strict German filtering', async ({ page }) => {
  await page.route('https://edu.yovisto.com/**', route => route.abort());
  await page.goto('/ili/i46593');
  await expect(page).toHaveURL(/\/view\/ili\/i46593$/);
  await expect(page.locator('.span-padding').filter({ hasText: 'cat (Noun)' }).first()).toBeVisible();
  await expect(page.locator('.span-padding').filter({ hasText: 'Katze' }).first()).toBeVisible();
  await page.goto('/de/ili/i46593');
  await expect(page.locator('mat-panel-title').first()).toContainText('Katze');
  await expect(page.locator('.search-results > mat-accordion > mat-expansion-panel')).toHaveCount(1);
});

test('live synset URLs and submitted IDs resolve one entry and respect its language', async ({ page, request }) => {
  await page.route('https://edu.yovisto.com/**', route => route.abort());
  const panels = page.locator('.search-results > mat-accordion > mat-expansion-panel');
  for (const path of ['/view/synset/ewn-02086723-n', '/view/en/synset/ewn-02086723-n']) {
    await page.goto(path);
    await expect(panels).toHaveCount(1);
    await expect(page.locator('mat-panel-title').first()).toContainText('dog (Noun)');
  }
  for (const path of ['/view/de/synset/ewn-02086723-n', '/view/synset/ewn-02086723-n?langs=de']) {
    await page.goto(path);
    await expect(page.locator('app-search')).toContainText('No results');
    await expect(panels).toHaveCount(0);
  }
  // An ILI still resolves language equivalents, each with its own native ID.
  const german = await request.get('/api/de/ili/i46360');
  expect(german.status()).toBe(200);
  const nativeId = (await german.json()).synsets[0].id;
  expect(nativeId).not.toBe('ewn-02086723-n');
  await page.goto('/view/synset/' + encodeURIComponent(nativeId));
  await expect(panels).toHaveCount(1);
  await expect(page.locator('mat-panel-title').first().locator('.fi-de')).toBeVisible();
  await page.goto('/');
  await page.getByRole('textbox').fill('ewn-02086723-n');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page).toHaveURL(/\/view\/synset\/ewn-02086723-n$/);
  await expect(panels).toHaveCount(1);
  await expect(page.locator('mat-panel-title').first()).toContainText('dog (Noun)');
});

test('live spouse search with all languages displays results promptly', async ({ page }) => {
  await page.route('https://edu.yovisto.com/**', route => route.abort());
  await page.goto('/');
  await page.getByRole('textbox').fill('spouse');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page).toHaveURL(/\/view\/lemma\/spouse$/);
  await expect(page.locator('mat-panel-title').first()).toContainText('spouse');
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('invalid identifiers show the backend error and missing concepts show no results', async ({ page }) => {
  await page.goto('/ili/not-an-ili');
  await expect(page.getByRole('alert')).toContainText('An ILI must');
  await page.goto('/synset/nonexistent-02124272-n');
  await expect(page.getByRole('alert')).toBeVisible();
  await page.goto('/ili/i9999999999');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.locator('app-search')).toContainText('No results');
});

test('legacy hash URLs and pasted links use the new router', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/#/search-wrapper');
  await expect(page).toHaveURL(/\/$/);
  await page.getByRole('textbox').fill('https://en-word.net/lemma/mouse');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page).toHaveURL(/\/view\/lemma\/mouse$/);
});

test('translations and relations keep the URL and search draft, with inline back history', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/lemma/mouse');
  const url = page.url();
  await page.getByRole('textbox').fill('next search');
  await page.locator('a').filter({ hasText: /^\s*Katze\s*$/ }).first().click();
  await expect(page.locator('mat-panel-title').first()).toContainText('Katze');
  await expect(page).toHaveURL(url);
  await expect(page.getByRole('textbox')).toHaveValue('next search');
  await page.locator('a[data-relation="hypernym"]').first().click();
  await expect(page.locator('mat-panel-title').first()).toContainText('hypernym');
  await expect(page.locator('app-search h2')).toContainText('Katze');
  await expect(page).toHaveURL(url);
  await page.getByRole('button', { name: 'Back to previous results' }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('Katze');
  await page.getByRole('button', { name: 'Back to previous results' }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await expect(page.getByRole('button', { name: 'Back to previous results' })).toHaveCount(0);
  await expect(page).toHaveURL(url);
  await expect(page.getByRole('textbox')).toHaveValue('next search');
  // Refresh reopens the explicitly entered lookup, rather than an inline step.
  await page.locator('a').filter({ hasText: /^\s*Katze\s*$/ }).first().click();
  await page.reload();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await expect(page.getByRole('textbox')).toHaveValue('');
});

test('synonyms and related-word details use the inline back button', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/lemma/mouse');
  const url = page.url();
  await page.locator('a').filter({ hasText: /^synonym$/ }).first().click();
  await expect(page.locator('mat-panel-title').first()).toContainText('synonym');
  await expect(page).toHaveURL(url);
  await expect(page.getByRole('textbox')).toHaveValue('');
  await page.getByRole('button', { name: 'Back to previous results' }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await page.locator('.no-bevel mat-expansion-panel-header').first().click();
  await page.locator('.no-bevel table a').first().click();
  await expect(page.locator('mat-panel-title').first()).toContainText('related word');
  await expect(page).toHaveURL(url);
  await expect(page.getByRole('textbox')).toHaveValue('');
  await page.getByRole('button', { name: 'Back to previous results' }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
});

test('submitting the same lookup restores the initial results and resets inline history', async ({ page }) => {
  await mockLookups(page);
  await page.goto('/lemma/mouse');
  const url = page.url();
  await page.locator('a').filter({ hasText: /^synonym$/ }).first().click();
  await expect(page.locator('mat-panel-title').first()).toContainText('synonym');
  await page.getByRole('textbox').fill('mouse');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await expect(page).toHaveURL(url);
  await expect(page.getByRole('textbox')).toHaveValue('');
  await expect(page.getByRole('button', { name: 'Back to previous results' })).toHaveCount(0);
  await page.locator('a').filter({ hasText: /^synonym$/ }).first().click();
  await page.getByRole('textbox').fill('dog');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page).toHaveURL(/\/view\/lemma\/dog$/);
  await expect(page.locator('mat-panel-title').first()).toContainText('dog');
  await expect(page.getByRole('button', { name: 'Back to previous results' })).toHaveCount(0);
  await page.goBack();
  await expect(page).toHaveURL(url);
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
});

test('inline back cancels a pending relation request', async ({ page }) => {
  await mockLookups(page);
  await page.route('**/api/dict/words/**', async route => {
    await new Promise(resolve => setTimeout(resolve, 600));
    await route.fulfill({ json: [word('en', 'late relation result')] });
  });
  await page.goto('/lemma/mouse');
  const pending = page.waitForRequest(request => request.url().includes('/api/dict/words/'));
  await page.locator('a[data-relation="hypernym"]').first().click();
  await pending;
  await page.getByRole('button', { name: 'Back to previous results' }).click();
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await page.waitForTimeout(800);
  await expect(page.locator('mat-panel-title').first()).toContainText('mouse');
  await expect(page).toHaveURL(/\/view\/lemma\/mouse$/);
});
