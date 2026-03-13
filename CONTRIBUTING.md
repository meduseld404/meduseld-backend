# Contributing to Meduseld

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. This is enforced automatically via git hooks.

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `perf`: Performance improvement
- `refactor`: Code refactoring
- `style`: UI/styling changes
- `docs`: Documentation only
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `build`: Build system changes
- `ci`: CI/CD changes

### Scopes

- `panel` - Control panel features
- `api` - API endpoints
- `auth` - Authentication
- `logs` - Logging system
- `config` - Configuration
- `monitoring` - Server monitoring
- `proxy` - Jellyfin/SSH proxy
- `health` - Health checks
- `backup` - Backup functionality
- `server` - Game server control
- `release` - Version releases

### Examples

```bash
feat(panel): add player count display
fix(auth): resolve redirect loop on macOS browsers
style(footer): update version to 0.4.0-alpha
refactor(routes): clean up catch-all route logic
docs(readme): update deployment instructions
```

### Using Commitizen (Recommended)

For an interactive commit prompt:

```bash
npm run commit
```

This will guide you through creating a properly formatted commit message.

### Setup for Contributors

1. Clone the repository
2. Run `npm install` to install dependencies
3. Husky will automatically set up git hooks
4. Use `npm run commit` or commit normally (validation will run automatically)

### Breaking Changes

For breaking changes, add `!` after the type:

```bash
feat(api)!: change authentication to Discord OAuth
```

### Pull Requests

- Keep PRs focused on a single feature or fix
- Write clear PR descriptions
- Reference related issues
- Ensure all commits follow the format
- Update CHANGELOG.md if needed
