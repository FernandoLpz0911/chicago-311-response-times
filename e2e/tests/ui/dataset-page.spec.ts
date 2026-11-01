import { test, expect } from '@playwright/test';
import { DatasetPage } from '../../pages/DatasetPage';

// Column display names for the fields the loader depends on.
const LOADER_COLUMNS = [
  'SR_NUMBER',
  'SR_TYPE',
  'STATUS',
  'ORIGIN',
  'CREATED_DATE',
  'CLOSED_DATE',
  'DUPLICATE',
  'COMMUNITY_AREA',
];

test.describe('311 Service Requests dataset page', () => {
  test('loads with the expected title and heading', async ({ page }) => {
    const dataset = new DatasetPage(page);
    await dataset.goto();
    await expect(page).toHaveTitle(DatasetPage.title);
    await expect(dataset.heading).toBeVisible();
  });

  test('lists the columns the pipeline loads', async ({ page }) => {
    const dataset = new DatasetPage(page);
    await dataset.goto();
    await expect(dataset.columnsSection).toBeVisible();
    await dataset.showAllColumns();
    for (const column of LOADER_COLUMNS) {
      await expect(dataset.columnName(column), column).toBeAttached();
    }
  });

  test('offers a CSV export', async ({ page }) => {
    const dataset = new DatasetPage(page);
    await dataset.goto();
    await dataset.exportButton.click();
    await dataset.exportFormat.click();
    await expect(dataset.csvOption).toBeVisible();
  });
});

test('catalog search finds the dataset', async ({ page }) => {
  await page.goto('/browse?q=311%20Service%20Requests', { waitUntil: 'domcontentloaded' });
  const result = page.getByRole('link', { name: '311 Service Requests', exact: true }).first();
  await expect(result).toBeVisible();
  await result.click();
  await expect(page).toHaveURL(/v6vf-nfxy/);
});
