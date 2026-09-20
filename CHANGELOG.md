# Changelog

## [2.1.0](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/compare/v2.0.0...v2.1.0) (2026-09-20)


### Features

* MWDS-438 disallow the faceted-search URL space in robots.txt ([#40](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/40)) ([644f413](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/644f4135acb2e05fd5bab13fee2b5a138f3d934a))


### Documentation

* add contributing and security policies ([#39](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/39)) ([27ecc8e](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/27ecc8e050ed557ce51e581ba48ca9177762a1f4))
* merging the release pull request is the release, not approving it ([#36](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/36)) ([f0b31f8](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/f0b31f84e3b8837dc9fd56b3230ae074df3027a6))

## [2.0.0](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/compare/v1.3.2...v2.0.0) (2026-09-18)


### ⚠ BREAKING CHANGES

* the mwlr_tracking plugin no longer exists. Remove it from ckan.plugins before upgrading, or CKAN will not start.

### Features

* MWDS-389 retire mwlr_tracking and use CKAN's own tracking ([0ec2fe3](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/0ec2fe3a77b6d11a476e86eb9f2b13ae55a01c9f))

## [1.3.2](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/compare/v1.3.1...v1.3.2) (2026-09-16)


### Fixes

* MWDS-444 wait for the Pipelines status, not any build status, before merging the pin ([#29](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/29)) ([74ec065](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/74ec065b12af9c06834544bebd836555824e4452))

## [1.3.1](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/compare/v1.3.0...v1.3.1) (2026-09-16)


### Fixes

* MWDS-446 a colour for the approvals environment marker ([#23](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/23)) ([539bfa3](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/539bfa3971080fafcf60dd83d29ed99e5ac82ce1))


### Documentation

* approving the release pull request is the release decision ([#26](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/26)) ([a0f7cdb](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/a0f7cdb92526f79432b26351d9c65e8c00ae64ea))

## [1.3.0](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/compare/v1.2.3...v1.3.0) (2026-09-16)


### Features

* MWDS-448 port the dataset approval workflow to this extension and CKAN 2.11+ ([#20](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/20)) ([e16d688](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/e16d688e88152a3c91e9d4d55a793782a8fe874a))


### Documentation

* MWDS-450 attribution for the dataset approval plugin ([#21](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/21)) ([f470037](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/f470037d97774a902401ab393337077d0f6173bb))

## [1.2.3](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/compare/v1.2.2...v1.2.3) (2026-09-16)


### Fixes

* MWDS-439 render the environment marker on full pages only ([#7](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/7)) ([a21ca72](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/a21ca72fdae7a45d46edb0bf32caa422564a4bba))
* MWDS-444 authenticate to Bitbucket with a repository access token ([#14](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/14)) ([008f41d](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/008f41d73cd1d02a168b9d42e2df4c52a2531a7b))
* MWDS-444 the commit message body broke the workflow YAML ([#12](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/issues/12)) ([ba5b8e4](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/commit/ba5b8e419a67d35b633d2541206f9f26029a6fbf))
