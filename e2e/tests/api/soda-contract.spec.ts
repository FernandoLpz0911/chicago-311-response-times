import { test, expect, type APIRequestContext } from '@playwright/test';

// These tests pin down what pipeline/extract.py and pipeline/transform.py assume about the
// live Socrata API. A failure here means the portal changed in a way that would break, or
// silently corrupt, the next load.

const RESOURCE = '/resource/v6vf-nfxy.json';
const METADATA = '/api/views/v6vf-nfxy.json';
const AREAS = '/resource/igwz-8jzy.json';

// Every source field the loader reads, with the Socrata type it expects.
const LOADER_FIELDS: Record<string, string> = {
  sr_number: 'text',
  sr_type: 'text',
  sr_short_code: 'text',
  owner_department: 'text',
  status: 'text',
  origin: 'text',
  created_date: 'calendar_date',
  closed_date: 'calendar_date',
  last_modified_date: 'calendar_date',
  duplicate: 'checkbox',
  legacy_record: 'checkbox',
  parent_sr_number: 'text',
  ward: 'number',
  community_area: 'number',
  latitude: 'number',
  longitude: 'number',
};

const FLOATING_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}$/;
const UTC_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;

// A narrow, fixed window keeps every query small and fast.
const ONE_DAY = "created_date >= '2024-06-03' AND created_date < '2024-06-04'";

type Row = Record<string, unknown>;

async function soql(request: APIRequestContext, params: Record<string, string>): Promise<Row[]> {
  const response = await request.get(RESOURCE, { params });
  expect(response.status(), await response.text()).toBe(200);
  return (await response.json()) as Row[];
}

test('dataset metadata still has every field the loader reads, with the same types', async ({
  request,
}) => {
  const response = await request.get(METADATA);
  expect(response.status()).toBe(200);
  const meta = (await response.json()) as {
    name: string;
    columns: { fieldName: string; dataTypeName: string }[];
  };
  expect(meta.name).toBe('311 Service Requests');
  const types = Object.fromEntries(meta.columns.map((c) => [c.fieldName, c.dataTypeName]));
  for (const [field, type] of Object.entries(LOADER_FIELDS)) {
    expect(types[field], `field ${field}`).toBe(type);
  }
});

// The loader's $select, as built by pipeline/extract.py: the 16 source fields, then the
// system fields.
const LOADER_SELECT = [...Object.keys(LOADER_FIELDS), ':id', ':updated_at'].join(',');

test('rows carry system fields and timestamps in the formats the parser expects', async ({
  request,
}) => {
  const rows = await soql(request, {
    $select: LOADER_SELECT,
    $where: ONE_DAY,
    $limit: '5',
  });
  expect(rows).toHaveLength(5);
  for (const row of rows) {
    expect(typeof row[':id']).toBe('string');
    expect(row[':updated_at']).toMatch(UTC_TIMESTAMP);
    expect(row.created_date).toMatch(FLOATING_TIMESTAMP);
    expect(typeof row.sr_number).toBe('string');
    expect(typeof row.duplicate).toBe('boolean');
  }
});

test('the loader $select is accepted and every named field comes back', async ({ request }) => {
  const rows = await soql(request, { $select: LOADER_SELECT, $where: ONE_DAY, $limit: '50' });
  // Socrata omits null fields per row, so a field is present if any returned row has it.
  const seen = new Set(rows.flatMap((r) => Object.keys(r)));
  for (const field of [...Object.keys(LOADER_FIELDS), ':id', ':updated_at']) {
    expect(seen.has(field), `field ${field}`).toBe(true);
  }
});

test('$where on created_date returns only rows inside the window', async ({ request }) => {
  const rows = await soql(request, { $where: ONE_DAY, $limit: '20' });
  expect(rows.length).toBeGreaterThan(0);
  for (const row of rows) {
    expect(String(row.created_date).startsWith('2024-06-03')).toBe(true);
  }
});

test('$limit caps the page size', async ({ request }) => {
  const rows = await soql(request, { $where: ONE_DAY, $limit: '7' });
  expect(rows).toHaveLength(7);
});

test('keyset paging on (:updated_at, :id) neither skips nor repeats rows', async ({
  request,
}) => {
  const base = { $select: ':id,:updated_at,sr_number', $order: ':updated_at,:id' };
  const ten = await soql(request, { ...base, $where: ONE_DAY, $limit: '10' });
  const first = await soql(request, { ...base, $where: ONE_DAY, $limit: '5' });
  const last = first[first.length - 1];
  const updatedAt = String(last[':updated_at']);
  const rowId = String(last[':id']);
  const second = await soql(request, {
    ...base,
    $where:
      `${ONE_DAY} AND (:updated_at > '${updatedAt}'` +
      ` OR (:updated_at = '${updatedAt}' AND :id > '${rowId}'))`,
    $limit: '5',
  });
  const paged = [...first, ...second].map((r) => r.sr_number);
  expect(paged).toEqual(ten.map((r) => r.sr_number));
});

test('keyset condition agrees with :id order inside one shared :updated_at', async ({
  request,
}) => {
  test.setTimeout(180_000);
  // :id order is Socrata's internal order, not lexicographic. The loader relies on
  // ':id >' and '$order=:id' agreeing within a timestamp, and one timestamp can hold
  // tens of thousands of rows.
  //
  // The portal re-stamps a large batch of rows (about 75k) roughly once a day, and while
  // that batch is being published its rows come and go between queries. Only look at
  // groups older than a day, which no longer change.
  const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 19);
  const [group] = await soql(request, {
    $select: ':updated_at,count(*) as n',
    $where: `:updated_at < '${dayAgo}'`,
    $group: ':updated_at',
    $order: 'n DESC',
    $limit: '1',
  });
  const updatedAt = String(group[':updated_at']);
  const order = { $select: ':id,:updated_at', $order: ':updated_at,:id' };
  const first = await soql(request, {
    ...order,
    $where: `:updated_at = '${updatedAt}'`,
    $limit: '3',
  });
  expect(first).toHaveLength(3);
  const [r1, r2, r3] = first;
  const next = await soql(request, {
    ...order,
    $where: `:updated_at = '${updatedAt}' AND :id > '${r1[':id']}'`,
    $limit: '2',
  });
  expect(next.map((r) => r[':id'])).toEqual([r2[':id'], r3[':id']]);
});

test('a malformed query is rejected with HTTP 400 and an error code', async ({ request }) => {
  const response = await request.get(RESOURCE, {
    params: { $where: 'no_such_column > 1', $limit: '1' },
  });
  expect(response.status()).toBe(400);
  const body = (await response.json()) as { errorCode?: string };
  expect(body.errorCode).toBeTruthy();
});

test('community areas dataset lists all 77 areas with number and name', async ({ request }) => {
  const response = await request.get(AREAS, {
    params: { $select: 'area_numbe,community', $limit: '100' },
  });
  expect(response.status()).toBe(200);
  const rows = (await response.json()) as { area_numbe: string; community: string }[];
  expect(rows).toHaveLength(77);
  const numbers = rows.map((r) => Number(r.area_numbe)).sort((a, b) => a - b);
  expect(numbers[0]).toBe(1);
  expect(numbers[76]).toBe(77);
  expect(rows.find((r) => r.area_numbe === '1')?.community).toBe('ROGERS PARK');
});
