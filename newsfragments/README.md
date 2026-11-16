# News fragments

Each user-visible change must come with a news fragment in this folder. The fragments are assembled into
`CHANGELOG.md` by [towncrier](https://towncrier.readthedocs.io/) when a release is created.

Create a file named `<pull request number>.<type>.md`, containing one sentence (Markdown) that describes the change
for the users. For instance `1234.fixed.md`:

    The propagation check of DNS challenges now verifies the TXT token value.

Available types:

* `added`: new features or options,
* `changed`: changes in existing behavior (displayed as "Modified"),
* `fixed`: bug fixes,
* `security`: security related changes,
* `removed`: removed or deprecated features.

If there is no pull request yet, or the change is not related to one, use an orphan fragment with a free name
prefixed by `+`, like `+short-description.added.md`.

You can create a fragment with `uv run towncrier create 1234.fixed.md`, and preview the changelog with
`uv run towncrier build --draft --version X.Y.Z`. Changes with no impact for users (tests, CI, internal refactoring)
do not need a fragment.
