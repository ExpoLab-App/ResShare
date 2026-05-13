import test from 'node:test';
import assert from 'node:assert/strict';
import ResShareClient from '../../src/index.js';

class MockFormData {
  constructor() {
    this.fields = [];
  }

  append(name, value, filename) {
    this.fields.push({ name, value, filename });
  }
}

const jsonResponse = (data, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  headers: {
    get: (name) => (name.toLowerCase() === 'content-type' ? 'application/json' : null)
  },
  json: async () => data
});

const jsonResponseWithCookies = (data, cookies, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  headers: {
    get: (name) => (name.toLowerCase() === 'content-type' ? 'application/json' : null),
    getSetCookie: () => cookies
  },
  json: async () => data
});

test('requires baseUrl', () => {
  assert.throws(() => new ResShareClient({}), /baseUrl/);
});

test('builds apiBase with prefix', () => {
  const client = new ResShareClient({
    baseUrl: 'http://localhost:5000/',
    apiPrefix: '/api/v1',
    fetch: async () => jsonResponse({}),
    FormData: MockFormData
  });

  assert.equal(client.apiBase, 'http://localhost:5000/api/v1');
});

test('login sends JSON body and credentials', async () => {
  let captured = null;
  const fetch = async (url, options) => {
    captured = { url, options };
    return jsonResponse({ message: 'SUCCESS' });
  };

  const client = new ResShareClient({
    baseUrl: 'http://localhost:5000',
    fetch,
    FormData: MockFormData
  });

  await client.auth.login({ username: 'alice', password: 'secret' });

  assert.equal(captured.url, 'http://localhost:5000/login');
  assert.equal(captured.options.method, 'POST');
  assert.equal(captured.options.credentials, 'include');
  assert.equal(captured.options.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(captured.options.body), {
    username: 'alice',
    password: 'secret'
  });
});

test('upload builds form data payload', async () => {
  let captured = null;
  const fetch = async (url, options) => {
    captured = { url, options };
    return jsonResponse({ message: 'SUCCESS' });
  };

  const client = new ResShareClient({
    baseUrl: 'http://localhost:5000',
    fetch,
    FormData: MockFormData
  });

  const file = { name: 'doc.txt' };
  await client.files.upload({ file, path: 'docs', skipProcessing: true });

  assert.equal(captured.url, 'http://localhost:5000/upload');
  assert.equal(captured.options.method, 'POST');
  assert.ok(captured.options.body instanceof MockFormData);

  const fields = captured.options.body.fields;
  const fieldMap = Object.fromEntries(fields.map((field) => [field.name, field]));

  assert.equal(fieldMap.path.value, 'docs');
  assert.equal(fieldMap.skip_ai_processing.value, 'true');
  assert.equal(fieldMap.file.filename, 'doc.txt');
});

test('remove share builds combined path', async () => {
  let captured = null;
  const fetch = async (url, options) => {
    captured = { url, options };
    return jsonResponse({ message: 'SUCCESS' });
  };

  const client = new ResShareClient({
    baseUrl: 'http://localhost:5000',
    fetch,
    FormData: MockFormData
  });

  await client.shares.remove({ fromUser: 'alice', path: 'docs' });

  assert.equal(captured.url, 'http://localhost:5000/delete');
  assert.equal(captured.options.method, 'DELETE');
  assert.deepEqual(JSON.parse(captured.options.body), {
    node_path: 'alice/docs',
    delete_in_root: false
  });
});

test('persists session cookie between requests in Node', async () => {
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options });
    if (calls.length === 1) {
      return jsonResponseWithCookies({ message: 'SUCCESS' }, ['session=abc123; Path=/; HttpOnly']);
    }
    return jsonResponse({ message: 'SUCCESS' });
  };

  const client = new ResShareClient({
    baseUrl: 'http://localhost:5000',
    fetch,
    FormData: MockFormData
  });

  await client.auth.login({ username: 'alice', password: 'secret' });
  await client.files.createFolder('docs');

  assert.equal(calls[1].options.headers.Cookie, 'session=abc123');
});
