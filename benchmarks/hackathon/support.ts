import { expect, test, type Browser, type Page, type TestInfo } from '@playwright/test';
import fs from 'node:fs';

type Body = (tools: {
  page: Page;
  browser: Browser;
  prepare: (name: string, action: () => Promise<void>) => Promise<void>;
  verify: (name: string, action: () => Promise<void>) => Promise<void>;
  blocked: (reason: string) => never;
}) => Promise<void>;

const selection = fs.existsSync('selection.json')
  ? JSON.parse(fs.readFileSync('selection.json', 'utf8')).scenario_id as string
  : null;

// scenario() declares tests from this module, so Playwright associates them with
// support.ts; configure the same file suite here rather than in importing specs.
test.use({ trace: 'on', screenshot: 'only-on-failure' });

export function scenario(id: string, name: string, body: Body) {
  if (selection && selection !== id) return;
  test(`${id} :: ${name}`, async ({ page, browser }, testInfo) => {
    test.setTimeout(90_000);
    const step = (phase: 'prepare' | 'verify') => async (label: string, action: () => Promise<void>) => {
      try {
        await test.step(`${phase}: ${label}`, action);
      } catch (error) {
        const outcome = phase === 'prepare' || message(error).startsWith('[blocked]') ? 'blocked' : 'failed';
        await attachPhase(testInfo, outcome, label, error);
        throw new Error(`[${outcome}] ${label}: ${message(error)}`);
      }
    };
    await body({
      page,
      browser,
      prepare: step('prepare'),
      verify: step('verify'),
      blocked: reason => { throw new Error(`[blocked] ${reason}`); },
    });
    await attachPhase(testInfo, 'passed', 'complete');
  });
}

async function attachPhase(testInfo: TestInfo, outcome: string, step: string, error?: unknown) {
  await testInfo.attach('hackathon-outcome', {
    body: JSON.stringify({ outcome, step, error: error ? message(error) : null }),
    contentType: 'application/json',
  });
}

function message(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export async function start(page: Page) {
  await page.goto('/');
  await expect(page.locator('body')).toBeVisible();
}

export async function signIn(page: Page, identity = 'alice.dev@example.test', password = 'Valid-password-123!') {
  await start(page);
  await page.getByRole('main').getByRole('link', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Username or email').fill(identity);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByText('alice-dev', { exact: true })).toBeVisible();
}

export async function openRepository(page: Page) {
  await start(page);
  await page.getByRole('link', { name: /acme-docs/i }).first().click();
  await expect(page.getByText(/acme-docs/i).first()).toBeVisible();
}

export async function openWorkbook(page: Page) {
  await start(page);
  await page.getByRole('link', { name: 'Q3 Sales', exact: true }).click();
  await expect(page.getByText('Q3 Sales', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('grid', { name: 'Worksheet grid' })).toBeVisible();
}

export function cell(page: Page, coordinate: string) {
  return page.getByRole('gridcell', { name: coordinate, exact: true });
}

export async function editCell(page: Page, coordinate: string, value: string) {
  await cell(page, coordinate).dblclick();
  const editor = page.getByRole('textbox', { name: `Edit ${coordinate}`, exact: true });
  await editor.fill(value);
  await editor.press('Enter');
}

export async function selectRange(page: Page, from: string, to: string) {
  await cell(page, from).dragTo(cell(page, to));
  await expect(cell(page, from)).toHaveAttribute('aria-selected', 'true');
  await expect(cell(page, to)).toHaveAttribute('aria-selected', 'true');
}

export { expect };
