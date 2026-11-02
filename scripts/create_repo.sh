#!/usr/bin/env bash
# Set up the aws-account-vending repo on your PERSONAL GitHub account, in 3 steps.
#
#   bash scripts/create_repo.sh create        # 1. own folder, .github, first commit, public repo, push
#   (create the GitHub App in the browser: docs/personal-setup.md step 3)
#   bash scripts/create_repo.sh connect-bot   # 2. store the App ID + private key in the repo
#   bash scripts/create_repo.sh test          # 3. send a test request, show the run and the PR
#
# Needs: git, GitHub CLI (brew install gh) logged in with `gh auth login`.
# Nothing here prints or stores your private key; gh sends it straight to GitHub's encrypted secrets.
set -euo pipefail

REPO_NAME="${REPO_NAME:-aws-account-vending}"
SRC="${SRC:-$HOME/MyLearning/AGENT/aws-account-vending}"     # where Claude put the files
DEST="${DEST:-$HOME/MyLearning/aws-account-vending}"         # the repo's own folder
ZIP="${ZIP:-$HOME/Downloads/aws-account-vending-github-folder.zip}"

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\n\033[31mError:\033[0m %s\n' "$*" >&2; exit 1; }

need_gh() {
  command -v gh >/dev/null || fail "GitHub CLI not found. Install it: brew install gh"
  gh auth status >/dev/null 2>&1 || fail "Not logged in to GitHub. Run: gh auth login"
  USER_NAME=$(gh api user --jq .login)
}

create() {
  need_gh
  say "GitHub user: $USER_NAME   repo: $USER_NAME/$REPO_NAME (public)"
  gh repo view "$USER_NAME/$REPO_NAME" >/dev/null 2>&1 && fail "$USER_NAME/$REPO_NAME already exists. Delete it or set REPO_NAME=another-name."

  say "1/5 Copy the project to its own folder: $DEST"
  [ -d "$SRC" ] || fail "Can't find $SRC"
  [ -e "$DEST" ] && fail "$DEST already exists. Move it away or set DEST=another/path."
  cp -R "$SRC" "$DEST"
  cd "$DEST"

  say "2/5 Add the .github folder (workflows, CODEOWNERS, rulesets)"
  if [ ! -d .github/workflows ]; then
    [ -f "$ZIP" ] || fail "Download aws-account-vending-github-folder.zip from the chat to ~/Downloads first."
    unzip -q "$ZIP" -d .
  fi
  ls .github/workflows

  say "3/5 Make you the code owner"
  bash scripts/setup_personal.sh "$USER_NAME"

  say "4/5 First commit on branch master"
  git init -q -b master
  git config user.name  >/dev/null || git config user.name  "$USER_NAME"
  git config user.email >/dev/null || git config user.email "$USER_NAME@users.noreply.github.com"
  git add .
  git commit -q -m "AWS account vending: first version"
  git log --oneline -1

  say "5/5 Create the public repo and push"
  gh repo create "$REPO_NAME" --public --source . --push \
     --description "AWS account vending: ServiceNow request -> Terraform PR -> reviewed merge"

  say "Done: https://github.com/$USER_NAME/$REPO_NAME"
  echo "Next: create the GitHub App (docs/personal-setup.md step 3), then run:"
  echo "  cd $DEST && bash scripts/create_repo.sh connect-bot"
}

connect_bot() {
  need_gh
  cd "$DEST" 2>/dev/null || true
  read -r -p "GitHub App ID (number at the top of the app's page): " APP_ID
  [[ "$APP_ID" =~ ^[0-9]+$ ]] || fail "App ID should be a number"
  default_pem=$(ls -t "$HOME"/Downloads/*.private-key.pem 2>/dev/null | head -1 || true)
  read -r -p "Private key file [${default_pem:-path to .pem}]: " PEM
  PEM="${PEM:-$default_pem}"
  [ -f "$PEM" ] || fail "File not found: $PEM"
  grep -q "BEGIN RSA PRIVATE KEY\|BEGIN PRIVATE KEY" "$PEM" || fail "$PEM doesn't look like a private key"

  gh variable set ACCOUNT_BOT_APP_ID --repo "$USER_NAME/$REPO_NAME" --body "$APP_ID"
  gh secret set ACCOUNT_BOT_PRIVATE_KEY --repo "$USER_NAME/$REPO_NAME" < "$PEM"
  say "Stored: variable ACCOUNT_BOT_APP_ID, secret ACCOUNT_BOT_PRIVATE_KEY"
  gh variable list --repo "$USER_NAME/$REPO_NAME"
  gh secret list --repo "$USER_NAME/$REPO_NAME"
  echo
  echo "Is the app installed on the repo? (App page > Install App > Only select repositories > $REPO_NAME)"
  echo "You can now delete $PEM, or move it somewhere safe. Never commit it."
  echo "Next: bash scripts/create_repo.sh test"
}

test_run() {
  need_gh
  say "Sending a test request (RITM0000001 / demo-sbx)"
  gh api "repos/$USER_NAME/$REPO_NAME/dispatches" --method POST --input - <<'EOF'
{"event_type": "aws-account-request",
 "client_payload": {"ritm": "RITM0000001", "sctask": "SCTASK0000001",
  "account_name": "demo-sbx", "app_team_name": "Demo", "support_group": "Demo Support",
  "technical_owner": "you@example.com", "budget_approver": "manager@example.com",
  "requested_for": "you@example.com"}}
EOF
  echo "Accepted. Waiting for the run to start..."
  sleep 8
  gh run list --repo "$USER_NAME/$REPO_NAME" --workflow account-request.yml --limit 1
  run_id=$(gh run list --repo "$USER_NAME/$REPO_NAME" --workflow account-request.yml --limit 1 --json databaseId --jq '.[0].databaseId')
  [ -n "$run_id" ] && gh run watch "$run_id" --repo "$USER_NAME/$REPO_NAME" --exit-status || true
  say "Pull requests:"
  gh pr list --repo "$USER_NAME/$REPO_NAME"
  echo
  echo "If a PR is listed: wait for the validate + plan checks, then add the approval rule:"
  echo "  gh api repos/$USER_NAME/$REPO_NAME/rulesets --method POST --input .github/rulesets/master-personal.json"
  echo "Then approve and merge the PR on github.com (docs/personal-setup.md steps 6-7)."
}

case "${1:-}" in
  create) create ;;
  connect-bot) connect_bot ;;
  test) test_run ;;
  *) sed -n '2,10p' "$0"; exit 1 ;;
esac
