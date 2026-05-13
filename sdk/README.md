# ResShare SDK (File Sharing)

JavaScript SDK for ResShare file sharing APIs. This package wraps the existing backend endpoints into a small, modular client that is easy to reuse across apps.

## Features
- Authentication helpers (login, signup, logout, status, delete user)
- File and folder operations (create folder, upload, delete, download)
- Sharing helpers (share, list shared, remove shared)
- Built-in retry logic and consistent error handling
- Cookie-based sessions by default (credentials included)

## Install
This repo does not publish the SDK yet. Use it directly from the `sdk/` folder or copy it into your project.

## Quick Start
```js
import ResShareClient from './sdk/src/index.js';

const client = new ResShareClient({
  baseUrl: 'http://localhost:5000'
});

await client.auth.login({ username: 'alice', password: 'secret' });

const folderResult = await client.files.createFolder('docs');
console.log(folderResult.status);

// Upload a file (browser)
const input = document.querySelector('input[type="file"]');
const file = input.files[0];
await client.files.upload({ file, path: 'docs', skipProcessing: true });

// Share a folder
await client.shares.share({ target: 'bob', path: 'docs' });
```

## Examples
- Basic: `node sdk/examples/basic-usage.js`
- End-to-end demo (upload, download, share, shared download, optional AI chat): `node sdk/examples/advanced-demo.js`

## API Surface
### Auth
- `client.auth.login({ username, password })`
- `client.auth.signup({ username, password })`
- `client.auth.logout()`
- `client.auth.status()`
- `client.auth.deleteUser({ password })`

### Files
- `client.files.createFolder(path)`
- `client.files.upload({ file, path, skipProcessing, filename })` (skipProcessing defaults to true)
- `client.files.deleteItem({ path, deleteInRoot })`
- `client.files.download({ path, isShared })` (returns a Response)
- `client.files.downloadZip({ path, isShared })` (returns a Response)

### Shares
- `client.shares.share({ target, path, node })`
- `client.shares.list()`
- `client.shares.remove({ combinedPath, fromUser, path })`

## Error Handling
All failed requests throw `ApiError` with `status` and `body` fields. The SDK also normalizes backend `message` or `result` into `status` when available.

```js
import { ApiError } from './sdk/src/index.js';

try {
  await client.files.createFolder('docs');
} catch (error) {
  if (error instanceof ApiError) {
    console.error(error.status, error.getUserMessage());
  }
}
```
