# Git Workflow

Work on review branches and keep commits scoped to the active task. Do not commit directly to `main`.

```bash
git checkout -b codex/frappe-foundation
git status
git add .
git commit -m "Build BEDO platform foundation"
git push -u origin codex/frappe-foundation
```

Split unrelated work into separate `codex/*` branches. Open draft pull requests and wait for review before merging. Do not force push shared branches. Inspect existing files before replacing or removing them.
