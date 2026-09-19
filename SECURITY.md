# Security policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting: the **Security** tab of this repository, then **Report a vulnerability**. That opens a private thread with the maintainers, and it is the only channel we watch for this.

**Please do not open a public issue, and do not put the details in a pull request.**

Tell us what the flaw is, how to reproduce it, and what an attacker gets out of it. A proof of concept helps; so does the version you tested, since this extension moves with the CKAN release it runs on.

What happens next:

- We acknowledge the report within **five working days** (New Zealand business days).
- We tell you what we think the impact is, and whether we agree it is a vulnerability here rather than upstream.
- We fix it and release, and we credit you in the advisory unless you would rather we did not.
- We publish an advisory once a fixed version is out.

If the flaw turns out to be in CKAN itself rather than in this extension, we will say so and point you at [CKAN's security policy](https://github.com/ckan/ckan/blob/master/SECURITY.md), which is where that report belongs. We would rather you sent it there ourselves than have us relay it second-hand.

## Scope

This repository: the `mwlr_datastore` and `dataset_approval` plugins, their templates, validators and schema.

Out of scope, and better sent elsewhere:

- **CKAN core and other extensions**: report to the project that owns the code.
- **Our hosted site.** Please do not run scans, fuzzers or exploit attempts against [datastore.landcareresearch.co.nz](https://datastore.landcareresearch.co.nz) or any other site we run. Reproduce it on your own CKAN instance. If a flaw can only be shown against ours, say so in the report and we will arrange it rather than you testing unannounced.

## Supported versions

We support the latest release. Fixes land on `main` and ship in the next version; we do not maintain older release lines for this extension.
