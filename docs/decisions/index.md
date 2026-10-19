# Decisions

Decisions about **this codebase**, recorded where the code is so they are reviewed in the same pull request as the change they justify.

These are **component ADRs**: internal to this extension, meaningful only next to it, and needing agreement from nobody outside its maintainers. They are numbered locally (`0001`, `0002`) and deliberately **do not** use the platform's area-prefixed scheme, so nothing here can be mistaken for a platform decision.

Decisions that reach beyond this repository - who may see which data, anything needing sign-off from data owners, security, IT operations or another team - are **platform ADRs** or design pages in Confluence. If a decision here turns out to matter more widely, it gets promoted there and leaves a pointer behind.

| | |
|---|---|
| [0001](0001-plugin-composition.md) | How the plugins in this extension fit together: order, permission labels, chained overrides |
