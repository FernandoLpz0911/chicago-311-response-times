import { type Locator, type Page } from '@playwright/test';

// The 311 Service Requests dataset page on the Chicago Data Portal.
export class DatasetPage {
  static readonly path = '/d/v6vf-nfxy';
  static readonly title = '311 Service Requests | City of Chicago | Data Portal';

  constructor(readonly page: Page) {}

  async goto(): Promise<void> {
    await this.page.goto(DatasetPage.path, { waitUntil: 'domcontentloaded' });
  }

  get heading(): Locator {
    return this.page.getByRole('heading', { level: 1, name: '311 Service Requests' });
  }

  get columnsSection(): Locator {
    return this.page.getByRole('heading', { name: /^Columns/ });
  }

  // The page-size dropdown has no accessible name, so scope it to the tab panel that
  // holds the Columns heading. No .first(): a second combobox there should fail loudly.
  get pageSizeSelect(): Locator {
    return this.page
      .getByRole('tabpanel')
      .filter({ has: this.columnsSection })
      .getByRole('combobox');
  }

  // The columns table shows 15 of 39 rows by default; switch the (unnamed)
  // page-size dropdown to 100 so every column name is in the page.
  async showAllColumns(): Promise<void> {
    await this.columnsSection.scrollIntoViewIfNeeded();
    await this.pageSizeSelect.click();
    await this.page.getByRole('option', { name: '100', exact: true }).click();
  }

  columnName(name: string): Locator {
    return this.page.getByText(name, { exact: true }).first();
  }

  get exportButton(): Locator {
    return this.page.getByRole('button', { name: /export/i }).first();
  }

  // The export dialog's format dropdown; its options render only once opened.
  get exportFormat(): Locator {
    return this.page.getByRole('combobox', { name: 'Export format' });
  }

  get csvOption(): Locator {
    return this.page.getByRole('option', { name: 'CSV', exact: true });
  }
}
