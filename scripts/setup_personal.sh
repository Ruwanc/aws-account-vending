#!/usr/bin/env bash
# One-time setup for testing on a PERSONAL GitHub account (public repo, no AWS).
#   bash scripts/setup_personal.sh <your-github-username>
# - CODEOWNERS: @YOUR-ORG/cloud-engineering -> @<username>  (teams only exist in organisations)
# - docs: YOUR-ORG -> <username>
# Safe to run twice. Revert with git if you move to the company repo.
set -euo pipefail
user="${1:?usage: bash scripts/setup_personal.sh <your-github-username>}"
cd "$(dirname "$0")/.."
sed -i.bak "s#@YOUR-ORG/cloud-engineering#@${user}#g" .github/CODEOWNERS && rm -f .github/CODEOWNERS.bak
for f in README.md docs/servicenow-flow.md docs/personal-setup.md; do
  [ -f "$f" ] && sed -i.bak "s#YOUR-ORG#${user}#g" "$f" && rm -f "$f.bak"
done
echo "CODEOWNERS now:"; grep -v '^#' .github/CODEOWNERS
echo "Next: follow docs/personal-setup.md from step 2."
