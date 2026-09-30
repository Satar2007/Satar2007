#!/usr/bin/env bash
# Commit only explicitly supplied generated files. Never force-push.
set -euo pipefail
if [[ $# -eq 0 || -z "${TARGET_BRANCH:-}" ]]; then
  echo 'Explicit asset paths and TARGET_BRANCH are required.' >&2
  exit 1
fi
for asset in "$@"; do
  [[ "$asset" == assets/generated/* && -s "$asset" ]] || { echo "Missing or invalid asset: $asset" >&2; exit 1; }
done
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- "$@"
if git diff --cached --quiet; then
  echo 'Generated assets are unchanged.'
  exit 0
fi
git commit -m 'chore: refresh profile visuals [skip ci]'
for attempt in 1 2 3; do
  git fetch origin "$TARGET_BRANCH"
  if ! git rebase "origin/$TARGET_BRANCH"; then
    git rebase --abort
    echo 'Asset update conflicts with another change; rerun this workflow.' >&2
    exit 1
  fi
  if git push origin "HEAD:$TARGET_BRANCH"; then exit 0; fi
done
echo 'Push failed after three attempts; inspect permissions or branch rules.' >&2
exit 1
