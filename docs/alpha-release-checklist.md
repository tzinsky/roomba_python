# Alpha Release Checklist

This checklist is for publishing the first `roomba_python` alpha release.

## 1. Quality Gates

- Run lint:
  - `python -m ruff check .`
- Run full tests:
  - `python -m pytest`
- Confirm schema conformance tests pass:
  - `tests/test_schema_conformance.py`
- Confirm workflows are present and green:
  - `.github/workflows/ci.yml`
  - `.github/workflows/package.yml`

## 2. Documentation Gates

- Verify core docs are current:
  - `docs/reduced-python-api-spec.md`
  - `docs/reduced-python-api-openapi-like.yaml`
  - `docs/reduced-python-api-openapi-companion.md`
  - `docs/node-to-python-method-mapping.md`
  - `docs/error-handling-boundary-map.md`
- Verify example index in `README.md` matches files under `examples/`.
- Verify migration notes include unsupported/changed behavior.

## 3. Packaging Gates

- Build artifacts:
  - `python -m build`
- Validate metadata:
  - `python -m twine check dist/*`
- Confirm `pyproject.toml` version is alpha-compatible (for example `0.1.0a0`).

## 4. Release Tag Preparation

Suggested first alpha tag:

- `v0.1.0-alpha.1`

Local tag commands:

```bash
git tag -a v0.1.0-alpha.1 -m "roomba_python alpha 1"
git show v0.1.0-alpha.1 --no-patch
```

Push tag:

```bash
git push origin v0.1.0-alpha.1
```

## 5. Post-Tag Verification

- Confirm CI/package workflows run for the tag.
- Publish release notes summarizing:
  - Reduced scope
  - Supported methods
  - Known gaps / out-of-scope features
  - Upgrade/migration notes from Node.js

## 6. Feedback Loop

- Open an alpha feedback issue template or tracking issue.
- Capture bugs and missing parity requests by category:
  - Command/API parity
  - Discovery/runtime behavior
  - Error handling/observability
  - Documentation clarity
