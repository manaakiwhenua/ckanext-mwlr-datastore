# Contributing

## About this repository

This extension is written for one CKAN site, [DataStore](https://datastore.landcareresearch.co.nz). It is published because the work is publicly funded, because the licence asks it of us, and because the CKAN community benefits from seeing how other people solved the same problems. It is not a general-purpose extension looking for users, and we do not promise to keep an API stable for anyone outside our own site.

So the door is open, but it is a normal-sized door:

- **Issues are welcome from anyone.** A bug you hit, a question about how something works, a thing the README gets wrong: open an issue.
- **Pull requests from outside our organisation: please open an issue first.** Not a formality. Most changes to this code have to fit a schema, a theme, and a deployment you cannot see from here, and it is unfair to let someone write a patch we then cannot take. An issue costs you a paragraph and tells you in a day or two whether a patch is worth your time.
- **Fork it freely.** If your site needs this extension to behave differently, a fork is a better answer than a setting we would both then have to maintain. The licence is written for that.

## Upstream first

Much of what this extension does is CKAN's job, done our way. When something is broken in CKAN core or in another extension, the fix belongs there, not here:

1. **Fix it upstream** where the bug is, and link the upstream issue or pull request from ours.
2. **Work around it here** only while the upstream fix is in flight, in a way that removes itself cleanly once it lands.
3. **Patch a dependency in our image** as a last resort, recorded with the upstream reference that justifies it.

We do not fork CKAN core. A local fix that quietly diverges from upstream is a cost we pay at every upgrade, and DataStore's upgrades are already large enough.

If you are here because of a bug you found in CKAN itself, [ckan/ckan](https://github.com/ckan/ckan) is the place to raise it, and CKAN's own [CONTRIBUTING guide](https://github.com/ckan/ckan/blob/master/CONTRIBUTING.rst) describes how that project takes patches.

## Reporting a bug

Open an issue with what you did, what happened, and what you expected. Say which CKAN version and which version of this extension you are running: the footer of a DataStore page shows both, and `pip show ckanext-mwlr-datastore` shows the extension's.

**Security problems do not go in an issue.** See [SECURITY.md](SECURITY.md).

## Making a change

Set up a CKAN development environment, then:

```sh
pip install -e .
pip install -r dev-requirements.txt
pytest --ckan-ini=test.ini ckanext/mwlr_datastore
```

Then:

- **One change per pull request.** A refactor riding along with a fix makes both harder to review and harder to revert.
- **Tests for behaviour that can be tested.** Validators and helpers can; a template's appearance mostly cannot, so say how you checked it instead.
- **Title the pull request in [Conventional Commits](https://www.conventionalcommits.org/) form** (`feat:`, `fix:`, `docs:`, `chore:`). We squash-merge, so the title becomes the commit on `main`, and the release tooling reads it to decide the next version and write the changelog. `fix:` gives a patch release, `feat:` a minor one, and a `!` or a `BREAKING CHANGE:` footer a major one.
- **Say what a breaking change breaks.** A configuration that must change before the new version starts is the kind of thing that belongs in the pull request body, where it ends up in the release notes.

Pull request builds run on GitHub-hosted runners: linting, and the test suite against a real CKAN. A first-time contributor's run waits for a maintainer to approve it, which is GitHub's default and not a judgement about you.

## Releasing

Every merge to `main` regenerates one open release pull request, opened by the `mwlr-release` App and titled for the next version. Merging that pull request is the release: it tags the version, publishes the GitHub release with the changelog, and opens the pull request that moves DataStore's pin to the new tag. Nothing merges it for you, and it is not edited by hand. The README's [Contributing](README.md#contributing) section has the detail.

## Licence

By contributing you agree that your contribution is licensed under [AGPL-3.0-or-later](LICENSE), the same licence as the rest of this repository. We ask for no copyright assignment and there is no contributor licence agreement to sign.
