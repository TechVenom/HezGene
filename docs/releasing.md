# Releasing HezGene to PyPI

This repo uses **GitHub Actions + PyPI Trusted Publishing** (OIDC) to publish releases.
No API tokens are stored in GitHub.

## 1) Bump version

Edit `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

Commit and push.

## 2) Configure Trusted Publishing (one-time)

You must do this once on **TestPyPI** and once on **PyPI**:

1. Create the project (first publish will also create it, but configuring ahead of time is easiest).
2. In the project’s settings, add a **Trusted Publisher**:
   - Provider: **GitHub**
   - Owner: `TechVenom`
   - Repository: `HezGene`
   - Workflow file:
     - TestPyPI: `.github/workflows/publish-testpypi.yml`
     - PyPI: `.github/workflows/publish-pypi.yml`
   - Environment: leave blank unless you explicitly configured environments.

## 3) Publish to TestPyPI

Create and push a tag like:

```bash
git tag vX.Y.Z-test
git push origin vX.Y.Z-test
```

This triggers `.github/workflows/publish-testpypi.yml`.

Install from TestPyPI:

```bash
python -m pip install -U pip
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple hezgene==X.Y.Z
hezgene --help
hezgene-demo
```

## 4) Publish to PyPI

Create and push the production tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

This triggers `.github/workflows/publish-pypi.yml`.

Install from PyPI:

```bash
pip install -U hezgene==X.Y.Z
```

