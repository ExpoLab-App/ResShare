import ResShareClient from '../src/index.js';

async function run() {
  const client = new ResShareClient({
    baseUrl: 'http://localhost:5000'
  });

  await client.auth.signup({ username: 'alice', password: 'Pass@123' });
  await client.auth.login({ username: 'alice', password: 'Pass@123' });

  const folder = await client.files.createFolder('docs');
  console.log('Create folder:', folder.status);

  const shares = await client.shares.list();
  console.log('Shared items:', shares.share_list || {});

  await client.auth.logout();
}

run().catch(error => {
  console.error('Example failed:', error);
});
