# Contributing
When contributing to the development of this repository, you shall use the following convention when naming Pull Requests

```bash
[TICKET-SLUG] <action(<module>)> <short name>
```

There are 6 different actions: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`. When pushing your code, use the most representative one for your PR.

```bash
[SS-1] feat(components) Add Sidebar Component
[SS-2] fix(types) Fix bug in typescript types
[SS-3] refactor(pages) Improve styling on home page
```

# Versioning
This project uses [Semantic Versioning](http://semver.org) to dictate how version numbers are assigned and incremented. Generally, we will include the appendix `rc` (vX.Y.Zrc1) to indicate whether the release is a `release candidate`. The release candidate appendix should only be used when the release has potential to be a stable product. Because of the nature of software development, the likelihood of not being production-ready is substantial because of involving many parties ( e.g. stakeholders ).

As per the Semantic Versioning rules, this project tracks the changes introduced in every release through the CHANGELOG.md file.

# Pre Commit Hooks
This repository has support for [pre-commit](https://pre-commit.com/) hooks. It is recommended to set up pre-commit hooks to ensure the code you commit meets our development standards.

Set up the pre-commit by running
```bash
poetry run pre-commit install 
```

Now `pre-commit` will run automatically on `git commit`!

## Bypassing Pre Commit Hooks
If by some reason you need to bypass pre commit checks, you might do so by adding the `--no-verify` flag on your commit

```
git commit -m <message> --no-verify
```