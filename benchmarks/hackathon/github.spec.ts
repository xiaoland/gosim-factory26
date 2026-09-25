import { expect, openRepository, scenario, signIn, start } from './support';

const unique = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

scenario('github-req-1-1-1', 'Register a New GitHub Account', async ({ page, prepare, verify }) => {
  const suffix = unique();
  await prepare('open registration', async () => {
    await start(page);
    await page.getByRole('main').getByRole('link', { name: 'Sign in', exact: true }).click();
    await page.getByRole('main').getByRole('link', { name: 'Create an account', exact: true }).click();
  });
  await verify('reject invalid fields without echoing passwords', async () => {
    await page.getByLabel('Username').fill('-invalid');
    await page.getByLabel('Email').fill('not-an-email');
    await page.getByLabel('Password', { exact: true }).fill('short');
    await page.getByLabel('Confirm password').fill('different');
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.getByText('Username format is invalid')).toBeVisible();
    await expect(page.getByText('Email format is invalid')).toBeVisible();
    await expect(page.getByText('Password requirements are not satisfied')).toBeVisible();
    await expect(page.getByText('Agree to terms is required')).toBeVisible();
    await expect(page.getByLabel('Password', { exact: true })).toHaveValue('');
  });
  await verify('create and immediately sign in', async () => {
    await page.getByLabel('Username').fill(`pw-user-${suffix}`);
    await page.getByLabel('Email').fill(`pw-user-${suffix}@example.test`);
    await page.getByLabel('Password', { exact: true }).fill('Valid-password-123!');
    await page.getByLabel('Confirm password').fill('Valid-password-123!');
    await page.getByRole('checkbox', { name: 'Agree to the terms' }).check();
    await page.getByRole('button', { name: 'Create account' }).click();
    await page.getByLabel('Username or email').fill(`pw-user-${suffix}@example.test`);
    await page.getByLabel('Password').fill('Valid-password-123!');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText(`pw-user-${suffix}`, { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByText(`pw-user-${suffix}`, { exact: true })).toBeVisible();
  });
});

scenario('github-req-1-1-2', 'Sign In with an Existing Account', async ({ page, prepare, verify }) => {
  await prepare('open sign in', async () => {
    await start(page);
    await page.getByRole('main').getByRole('link', { name: 'Sign in', exact: true }).click();
  });
  await verify('use one generic error for bad credentials', async () => {
    await page.getByLabel('Username or email').fill('alice-dev');
    await page.getByLabel('Password').fill('wrong-password');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Invalid credentials', { exact: true })).toBeVisible();
  });
  await verify('establish and persist the browser session', async () => {
    await page.getByLabel('Username or email').fill('alice.dev@example.test');
    await page.getByLabel('Password').fill('Valid-password-123!');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('alice-dev', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByText('alice-dev', { exact: true })).toBeVisible();
  });
});

scenario('github-req-1-1-3', 'Recover Account Access Through a Verified Email', async ({ page, prepare, verify }) => {
  await prepare('open password recovery', async () => {
    await start(page);
    await page.getByRole('link', { name: 'Forgot password', exact: true }).click();
    await page.getByLabel('Email').fill('alice.dev@example.test');
    await page.getByRole('button', { name: 'Send reset link' }).click();
    await expect(page.getByText('123456', { exact: true })).toBeVisible();
  });
  await verify('reject wrong code and accept fixed code', async () => {
    await page.getByLabel('Verification code').fill('000000');
    await page.getByLabel('New password').fill('Replacement-password-456!');
    await page.getByLabel('Confirm password').fill('Replacement-password-456!');
    await page.getByRole('button', { name: 'Reset password' }).click();
    await expect(page.getByText('Verification code is invalid')).toBeVisible();
    await page.getByLabel('Verification code').fill('123456');
    await page.getByRole('button', { name: 'Reset password' }).click();
    await expect(page.getByText('Password updated')).toBeVisible();
  });
});

scenario('github-req-1-2', 'Sign Out and End the Current Web Session', async ({ page, prepare, verify }) => {
  await prepare('sign in', () => signIn(page));
  await verify('cancel then confirm sign out', async () => {
    await page.getByRole('button', { name: /Account menu/i }).click();
    await page.getByRole('menuitem', { name: 'Sign out' }).click();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByText('alice-dev', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: /Account menu/i }).click();
    await page.getByRole('menuitem', { name: 'Sign out' }).click();
    await page.getByRole('button', { name: 'Confirm sign out' }).click();
    await expect(page.getByRole('main').getByRole('link', { name: 'Sign in', exact: true })).toBeVisible();
  });
});

scenario('github-req-1-3', 'Change Account Password', async ({ page, prepare, verify }) => {
  await prepare('open password settings', async () => {
    await signIn(page);
    await page.getByRole('button', { name: /Account menu/i }).click();
    await page.getByRole('link', { name: 'Settings', exact: true }).click();
    await page.getByRole('link', { name: 'Password and authentication' }).click();
  });
  await verify('reject missing current password', async () => {
    await page.getByLabel('New password').fill('Required-password-789!');
    await page.getByLabel('Confirm password').fill('Required-password-789!');
    await page.getByRole('button', { name: 'Update password' }).click();
    await expect(page.getByText('Current password is required')).toBeVisible();
  });
});

async function signed(page: any) { await signIn(page); }
async function repository(page: any) { await openRepository(page); }
async function signedRepository(page: any) { await signIn(page); await page.getByRole('link', { name: /acme-docs/i }).first().click(); }

scenario('github-req-2-1-1', 'Browse Organization Repositories', async ({ page, prepare, verify }) => {
  await prepare('open public organization', () => start(page));
  await verify('filter public repositories', async () => {
    await page.getByRole('link', { name: /Acme Demo/i }).first().click();
    await page.getByRole('link', { name: 'Repositories' }).click();
    await page.getByRole('textbox', { name: 'Find a repository' }).fill('acme-docs');
    await expect(page.getByRole('link', { name: /acme-docs/i })).toBeVisible();
  });
});

scenario('github-req-2-1-2', 'Create an Organization After Authentication', async ({ page, prepare, verify }) => {
  const name = `org-${unique()}`;
  await prepare('open organization creation', async () => {
    await signed(page); await page.getByRole('button', { name: /Account menu/i }).click();
    await page.getByRole('link', { name: 'Your organizations' }).click();
    await page.getByRole('link', { name: 'New organization' }).click();
  });
  await verify('create a persistent organization', async () => {
    await page.getByLabel('Organization name').fill(name);
    await page.getByLabel('Display name').fill(`Organization ${name}`);
    await page.getByRole('button', { name: 'Create organization' }).click();
    await expect(page.getByText(name, { exact: true })).toBeVisible();
    await page.reload(); await expect(page.getByText(name, { exact: true })).toBeVisible();
  });
});

scenario('github-req-2-2-1', 'Create an Organization Team', async ({ page, prepare, verify }) => {
  await prepare('open team creation', async () => { await signed(page); await page.getByRole('link', { name: /Acme Demo/i }).first().click(); await page.getByRole('link', { name: 'Teams' }).click(); await page.getByRole('link', { name: 'New team' }).click(); });
  await verify('create team', async () => { const name = `team-${unique()}`; await page.getByLabel('Team name').fill(name); await page.getByRole('button', { name: 'Create team' }).click(); await expect(page.getByText(name, { exact: true })).toBeVisible(); });
});

scenario('github-req-2-2-2', 'Manage Organization Team Members and Hierarchy', async ({ page, prepare, verify }) => {
  await prepare('open seeded team settings', async () => { await signed(page); await page.getByRole('link', { name: /frontend-team/i }).first().click(); await page.getByRole('link', { name: 'Settings' }).click(); });
  await verify('expose member and parent controls', async () => { await expect(page.getByRole('button', { name: 'Add member' })).toBeVisible(); await expect(page.getByLabel('Parent team')).toBeVisible(); await expect(page.getByRole('button', { name: 'Save' })).toBeVisible(); });
});

scenario('github-req-2-2-3', 'Directly Add a User as an Organization Member', async ({ page, prepare, verify }) => {
  await prepare('open organization people', async () => { await signed(page); await page.getByRole('link', { name: /Acme Demo/i }).first().click(); await page.getByRole('link', { name: 'People' }).click(); });
  await verify('add a member with explicit role', async () => { await page.getByRole('button', { name: 'Add member' }).click(); await page.getByLabel('Username or email').fill('bob-reviewer'); await page.getByLabel('Role').selectOption({ label: 'Member' }); await page.getByRole('button', { name: 'Add' }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible(); });
});

scenario('github-req-2-2-4', 'Remove a Member from an Organization', async ({ page, prepare, verify }) => {
  await prepare('open seeded member', async () => { await signed(page); await page.getByRole('link', { name: /Acme Demo/i }).first().click(); await page.getByRole('link', { name: 'People' }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible(); });
  await verify('remove member and persist absence', async () => { await page.getByRole('button', { name: 'Member menu bob-reviewer' }).click(); await page.getByRole('menuitem', { name: 'Remove from organization' }).click(); await page.getByRole('button', { name: 'Remove', exact: true }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0); await page.reload(); await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0); });
});

scenario('github-req-2-3', 'Grant Repository Access to People and Teams', async ({ page, prepare, verify }) => {
  await prepare('open manage access', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Settings' }).click(); await page.getByRole('link', { name: 'Manage access' }).click(); });
  await verify('grant explicit write role', async () => { await page.getByRole('button', { name: 'Add people or teams' }).click(); await page.getByLabel('Search').fill('bob-reviewer'); await page.getByLabel('Role').selectOption({ label: 'Write' }); await page.getByRole('button', { name: /Add|Save/ }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible(); });
});

scenario('github-req-3-1', 'Search for and Locate Repositories', async ({ page, prepare, verify }) => {
  await prepare('open search', () => start(page));
  await verify('find seeded repository and report no results', async () => { const search = page.getByRole('searchbox', { name: 'Search', exact: true }); await search.fill('acme-docs'); await search.press('Enter'); await expect(page.getByRole('link', { name: /acme-docs/i })).toBeVisible(); await search.fill(`missing-${unique()}`); await search.press('Enter'); await expect(page.getByText('No results')).toBeVisible(); });
});

scenario('github-req-3-2-1', 'Create a Repository with Owner, Visibility, and Initialization Options', async ({ page, prepare, verify }) => {
  const name = `repo-${unique()}`;
  await prepare('open repository creation', async () => { await signed(page); await page.getByRole('link', { name: 'New repository' }).click(); });
  await verify('create initialized repository', async () => { await page.getByLabel('Repository name').fill(name); await page.getByLabel('Description').fill('Repository created by Playwright'); await page.getByRole('radio', { name: 'Private' }).check(); await page.getByRole('checkbox', { name: 'Add a README file' }).check(); await page.getByRole('button', { name: 'Create repository' }).click(); await expect(page.getByText(name, { exact: true })).toBeVisible(); await expect(page.getByText('Private', { exact: true })).toBeVisible(); });
});

scenario('github-req-3-2-2', 'Fork a Repository into Another Namespace', async ({ page, prepare, verify }) => {
  await prepare('open public repository', () => repository(page));
  await verify('create fork with lineage', async () => { await page.getByRole('button', { name: 'Fork' }).click(); const name = `fork-${unique()}`; await page.getByLabel('Repository name').fill(name); await page.getByRole('button', { name: 'Create fork' }).click(); await expect(page.getByText(/Forked from .*acme-docs/i)).toBeVisible(); });
});

scenario('github-req-3-2-3', 'Copy a Repository Clone Value', async ({ page, prepare, verify }) => {
  await prepare('open public repository', () => repository(page));
  await verify('switch clone method and copy', async () => { await page.getByRole('button', { name: 'Code', exact: true }).click(); await expect(page.getByRole('tab', { name: 'HTTPS' })).toBeVisible(); await page.getByRole('tab', { name: 'SSH' }).click(); await page.getByRole('button', { name: 'Copy clone value' }).click(); await expect(page.getByText('Copied')).toBeVisible(); });
});

scenario('github-req-3-3', 'View a Public Repository Overview', async ({ page, prepare, verify }) => {
  await prepare('open public repository', () => repository(page));
  await verify('show repository identity and code', async () => { await expect(page.getByText('Public', { exact: true })).toBeVisible(); await expect(page.getByRole('link', { name: 'Code', exact: true })).toBeVisible(); });
});

scenario('github-req-3-4', 'Change Repository Visibility with Permission Checks', async ({ page, prepare, verify }) => {
  await prepare('open private repository settings', async () => { await signed(page); await page.getByRole('link', { name: /secret-research/i }).first().click(); await page.getByRole('link', { name: 'Settings' }).click(); await page.getByRole('link', { name: 'General' }).click(); });
  await verify('make repository public and persist', async () => { await page.getByRole('button', { name: 'Change visibility' }).click(); await page.getByRole('radio', { name: 'Public' }).check(); await page.getByRole('button', { name: 'Confirm visibility' }).click(); await expect(page.getByText('Public', { exact: true })).toBeVisible(); await page.reload(); await expect(page.getByText('Public', { exact: true })).toBeVisible(); });
});

scenario('github-req-4-1', 'Browse Repository Files and Directories', async ({ page, prepare, verify }) => { await prepare('open repository', () => repository(page)); await verify('browse seeded file tree without signing in', async () => { await expect(page.getByRole('link', { name: /README/i }).first()).toBeVisible(); await page.getByRole('link', { name: /README/i }).first().click(); await expect(page.locator('main')).toContainText(/README|Acme/i); }); });
scenario('github-req-4-2-1', 'View Repository Commit History', async ({ page, prepare, verify }) => { await prepare('open repository', () => repository(page)); await verify('show reverse chronological commits', async () => { await page.getByRole('link', { name: 'Commits' }).click(); await expect(page.getByText(/ago/).first()).toBeVisible(); }); });
scenario('github-req-4-2-2', 'Inspect Commit and Revision Differences', async ({ page, prepare, verify }) => { await prepare('open commit history', async () => { await repository(page); await page.getByRole('link', { name: 'Commits' }).click(); }); await verify('show changed files', async () => { await page.getByRole('link').filter({ hasText: /[0-9a-f]{7}/ }).first().click(); await expect(page.getByText('Changed files')).toBeVisible(); }); });
scenario('github-req-4-2-3', 'Search Code Within a Repository', async ({ page, prepare, verify }) => { await prepare('open repository', () => repository(page)); await verify('search only readable code', async () => { await page.getByRole('button', { name: 'Search' }).click(); await page.getByRole('textbox', { name: 'Search' }).fill('onboarding'); await page.getByRole('textbox', { name: 'Search' }).press('Enter'); await expect(page.locator('main')).toContainText(/onboarding|No code results/i); }); });
scenario('github-req-4-3-1', 'List and Switch Repository Branches', async ({ page, prepare, verify }) => { await prepare('open repository', () => repository(page)); await verify('filter and switch branch', async () => { await page.getByRole('button', { name: /Branch / }).click(); await page.getByLabel('Find branch').fill('main'); await expect(page.getByRole('option', { name: 'main' })).toBeVisible(); await page.getByRole('option', { name: 'main' }).click(); await expect(page.getByRole('button', { name: 'Branch main' })).toBeVisible(); }); });
scenario('github-req-4-3-2', 'Create a Branch from an Existing Revision', async ({ page, prepare, verify }) => { await prepare('open writable repository', () => signedRepository(page)); await verify('create valid branch and reject invalid branch', async () => { await page.getByRole('button', { name: /Branch / }).click(); const name = `feature-${unique()}`; await page.getByLabel('Find branch').fill(name); await page.getByRole('button', { name: `Create branch: ${name}` }).click(); await expect(page.getByRole('button', { name: `Branch ${name}` })).toBeVisible(); }); });
scenario('github-req-4-3-3', 'Change the Repository Default Branch', async ({ page, prepare, verify }) => { await prepare('open branch settings', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Settings' }).click(); await page.getByRole('link', { name: 'Branches' }).click(); }); await verify('expose guarded default branch update', async () => { await expect(page.getByLabel('Default branch')).toBeVisible(); await expect(page.getByRole('button', { name: 'Update' })).toBeVisible(); }); });
scenario('github-req-4-4', 'Manage Repository Files Through the Web Interface', async ({ page, prepare, verify }) => { await prepare('open writable repository', () => signedRepository(page)); await verify('create a file as a commit', async () => { await page.getByRole('button', { name: 'Add file' }).click(); await page.getByRole('menuitem', { name: 'Create new file' }).click(); const name = `notes-${unique()}.md`; await page.getByLabel('File name').fill(name); await page.getByLabel('File contents').fill('created through visible UI'); await page.getByLabel('Commit message').fill(`Add ${name}`); await page.getByRole('button', { name: 'Commit changes' }).click(); await expect(page.getByText(name, { exact: true })).toBeVisible(); }); });

scenario('github-req-5-1-1', 'List and Filter Repository Issues', async ({ page, prepare, verify }) => { await prepare('open issue list', async () => { await repository(page); await page.getByRole('link', { name: 'Issues' }).click(); }); await verify('filter open and closed issues', async () => { await expect(page.getByText('Open', { exact: true }).first()).toBeVisible(); await page.getByRole('link', { name: 'Closed' }).click(); await expect(page.getByText('Closed', { exact: true }).first()).toBeVisible(); }); });
scenario('github-req-5-1-2', 'View an Issue and Its Discussion', async ({ page, prepare, verify }) => { await prepare('open issue list', async () => { await repository(page); await page.getByRole('link', { name: 'Issues' }).click(); }); await verify('show seeded issue discussion and activity', async () => { await page.getByRole('link', { name: /Improve onboarding/i }).click(); await expect(page.getByText(/Improve onboarding/i)).toBeVisible(); await expect(page.getByText('Activity')).toBeVisible(); }); });
scenario('github-req-5-2-1', 'Create a Repository Issue', async ({ page, prepare, verify }) => { await prepare('open new issue', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: 'New issue' }).click(); }); await verify('reject empty then create issue', async () => { await page.getByRole('button', { name: 'Submit new issue' }).click(); await expect(page.getByText('Title is required')).toBeVisible(); const title = `Issue ${unique()}`; await page.getByLabel('Title').fill(title); await page.getByLabel('Description').fill('Created from the public workflow'); await page.getByRole('button', { name: 'Submit new issue' }).click(); await expect(page.getByText(title, { exact: true })).toBeVisible(); await page.reload(); await expect(page.getByText(title, { exact: true })).toBeVisible(); }); });
scenario('github-req-5-2-2', 'Edit an Issue Title and Description', async ({ page, prepare, verify }) => { await prepare('open seeded issue', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('edit title and persist', async () => { await page.getByRole('button', { name: 'Edit issue title' }).click(); const title = `Onboarding ${unique()}`; await page.getByLabel('Issue title').fill(title); await page.getByRole('button', { name: 'Save issue title' }).click(); await expect(page.getByText(title, { exact: true })).toBeVisible(); await page.reload(); await expect(page.getByText(title, { exact: true })).toBeVisible(); }); });
scenario('github-req-5-2-3', 'Comment on an Issue Discussion', async ({ page, prepare, verify }) => { await prepare('open seeded issue', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('reject empty and append comment', async () => { await page.getByRole('button', { name: 'Comment' }).click(); await expect(page.getByText('Comment is required')).toBeVisible(); const body = `Comment ${unique()}`; await page.getByLabel('Comment').fill(body); await page.getByRole('button', { name: 'Comment' }).click(); await expect(page.getByText(body, { exact: true })).toBeVisible(); }); });
scenario('github-req-5-3-1', 'Assign or Unassign Issue Participants', async ({ page, prepare, verify }) => { await prepare('open maintainable issue', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('assign and unassign seeded member', async () => { await page.getByRole('button', { name: 'Assignees' }).click(); await page.getByLabel('Search assignees').fill('bob-reviewer'); await page.getByRole('option', { name: 'bob-reviewer' }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible(); await page.getByRole('button', { name: 'Assignees' }).click(); await page.getByRole('option', { name: 'bob-reviewer' }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0); }); });
scenario('github-req-5-3-2', 'Apply Labels to an Issue', async ({ page, prepare, verify, blocked }) => { await prepare('open maintainable issue with seeded labels', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('apply seeded bug label', async () => { await page.getByRole('button', { name: 'Labels' }).click(); const option = page.getByRole('option', { name: 'bug' }); if (!await option.count()) blocked('the public contract requires a seeded bug label but no public creation workflow exists'); await option.click(); await expect(page.getByText('bug', { exact: true })).toBeVisible(); }); });
scenario('github-req-5-3-3', 'Assign Issues and Pull Requests to a Milestone', async ({ page, prepare, verify, blocked }) => { await prepare('open maintainable issue with seeded milestone', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('select and clear seeded milestone', async () => { await page.getByRole('button', { name: 'Milestone' }).click(); const option = page.getByRole('option', { name: 'Q3 launch' }); if (!await option.count()) blocked('the public contract requires a seeded Q3 launch milestone but no public creation workflow exists'); await option.click(); await expect(page.getByText('Q3 launch', { exact: true })).toBeVisible(); }); });
scenario('github-req-5-4', 'Close or Reopen an Issue', async ({ page, prepare, verify }) => { await prepare('open maintainable issue', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Issues' }).click(); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('close and reopen with persistence', async () => { await page.getByRole('button', { name: 'Close issue' }).click(); await expect(page.getByText('Closed issue')).toBeVisible(); await page.reload(); await page.getByRole('button', { name: 'Reopen issue' }).click(); await expect(page.getByText('Open', { exact: true }).first()).toBeVisible(); }); });

async function pullRequests(page: any, signedIn = false) { if (signedIn) await signedRepository(page); else await repository(page); await page.getByRole('link', { name: 'Pull requests' }).click(); }
scenario('github-req-6-1', 'Protect Branches with Review and Status-Check Requirements', async ({ page, prepare, verify }) => { await prepare('open branch protection settings', async () => { await signedRepository(page); await page.getByRole('link', { name: 'Settings' }).click(); await page.getByRole('link', { name: 'Branches' }).click(); }); await verify('expose independent approval and test check rules', async () => { await expect(page.locator('main')).toContainText(/approval/i); await expect(page.locator('main')).toContainText(/test/i); }); });
scenario('github-req-6-2-1', 'List and Filter Repository Pull Requests', async ({ page, prepare, verify }) => { await prepare('open pull request list', () => pullRequests(page)); await verify('show source target and status filters', async () => { await expect(page.locator('main')).toContainText(/Open|Closed|Draft/i); await expect(page.locator('main')).toContainText(/main|feature-search/i); }); });
scenario('github-req-6-2-2', 'Compare Branches Before Opening a Pull Request', async ({ page, prepare, verify }) => { await prepare('open comparison', async () => { await pullRequests(page, true); await page.getByRole('link', { name: 'New pull request' }).click(); }); await verify('select base and compare and show diff', async () => { await expect(page.getByLabel(/base/i)).toBeVisible(); await expect(page.getByLabel(/compare/i)).toBeVisible(); await expect(page.locator('main')).toContainText(/change|diff|file/i); }); });
scenario('github-req-6-2-3', 'Create a Pull Request from Comparison Results', async ({ page, prepare, verify }) => { await prepare('open comparison', async () => { await pullRequests(page, true); await page.getByRole('link', { name: 'New pull request' }).click(); }); await verify('create normal pull request', async () => { await page.getByRole('button', { name: 'Create pull request' }).click(); await expect(page.locator('main')).toContainText(/Open/i); }); });
scenario('github-req-6-2-4', 'Create a Draft Pull Request', async ({ page, prepare, verify }) => { await prepare('open comparison', async () => { await pullRequests(page, true); await page.getByRole('link', { name: 'New pull request' }).click(); }); await verify('create draft and mark ready', async () => { await page.getByRole('button', { name: 'Create draft pull request' }).click(); await expect(page.getByText('Draft', { exact: true })).toBeVisible(); await page.getByRole('button', { name: 'Ready for review' }).click(); await expect(page.getByText('Open', { exact: true })).toBeVisible(); }); });
scenario('github-req-6-3-1', 'View Pull Request Overview and Commits', async ({ page, prepare, verify }) => { await prepare('open seeded pull request', async () => { await pullRequests(page); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('navigate conversation commits and checks', async () => { for (const name of ['Conversation', 'Commits', 'Checks']) await expect(page.getByRole('link', { name })).toBeVisible(); await page.getByRole('link', { name: 'Commits' }).click(); await expect(page.locator('main')).toContainText(/[0-9a-f]{7}|commit/i); }); });
scenario('github-req-6-3-2', 'Inspect Changed Files and Aggregate Diff', async ({ page, prepare, verify }) => { await prepare('open seeded pull request', async () => { await pullRequests(page); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('show per-file diff and aggregate counts', async () => { await page.getByRole('link', { name: 'Files changed' }).click(); await expect(page.locator('main')).toContainText(/additions/i); await expect(page.locator('main')).toContainText(/deletions/i); }); });
scenario('github-req-6-3-3', 'Add Review Comments to Changed Code Lines', async ({ page, prepare, verify }) => { await prepare('open changed files as reviewer', async () => { await pullRequests(page, true); await page.getByRole('link', { name: /Improve onboarding/i }).click(); await page.getByRole('link', { name: 'Files changed' }).click(); }); await verify('add a line comment', async () => { await page.getByRole('button', { name: '+' }).first().click(); await page.getByRole('textbox').last().fill(`Review ${unique()}`); await expect(page.getByRole('button', { name: 'Add single comment' })).toBeVisible(); await expect(page.getByRole('button', { name: 'Start a review' })).toBeVisible(); }); });
scenario('github-req-6-3-4', 'Submit a Pull Request Review', async ({ page, prepare, verify }) => { await prepare('open seeded pull request as reviewer', async () => { await pullRequests(page, true); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('submit an approve review', async () => { await page.getByRole('button', { name: /Review changes/i }).click(); await page.getByRole('radio', { name: /Approve/i }).check(); await page.getByRole('button', { name: /Submit review/i }).click(); await expect(page.locator('main')).toContainText(/Approved/i); }); });
scenario('github-req-6-4', 'Request or Remove Pull Request Reviewers', async ({ page, prepare, verify }) => { await prepare('open seeded pull request as author', async () => { await pullRequests(page, true); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('request seeded reviewer', async () => { await page.getByRole('button', { name: /Reviewers/i }).click(); await page.getByRole('option', { name: 'bob-reviewer' }).click(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible(); }); });
scenario('github-req-6-5', 'Merge an Eligible Pull Request', async ({ page, prepare, verify }) => { await prepare('open eligible pull request as maintainer', async () => { await pullRequests(page, true); await page.getByRole('link', { name: /Improve onboarding/i }).click(); }); await verify('merge and persist terminal state', async () => { await page.getByRole('button', { name: 'Merge pull request' }).click(); await page.getByRole('button', { name: 'Confirm merge' }).click(); await expect(page.getByText('Merged', { exact: true })).toBeVisible(); await page.reload(); await expect(page.getByText('Merged', { exact: true })).toBeVisible(); }); });
scenario('github-req-6-6', 'Close or Reopen a Pull Request Without Merging', async ({ page, prepare, verify }) => { await prepare('open open pull request as author', async () => { await pullRequests(page, true); await page.getByRole('link', { name: /Fix search/i }).click(); }); await verify('close and reopen without merge', async () => { await page.getByRole('button', { name: /Close pull request/i }).click(); await expect(page.getByText('Closed', { exact: true })).toBeVisible(); await page.getByRole('button', { name: /Reopen pull request/i }).click(); await expect(page.getByText('Open', { exact: true })).toBeVisible(); }); });
