#!/bin/bash
set -e
cd ~ || exit

echo "Setting Up Bench..."

pip install frappe-bench
bench -v init frappe-bench --skip-assets --skip-redis-config-generation --python "$(which python)" --frappe-branch develop
cd ./frappe-bench || exit

echo "Get FCRM..."
bench get-app --skip-assets crm "${GITHUB_WORKSPACE}"

echo "Generating POT file..."
bench generate-pot-file --app crm

cd ./apps/crm || exit

echo "Configuring git user..."
git config user.email "developers@erpnext.com"
git config user.name "frappe-pr-bot"

echo "Setting the correct git remote..."
# Here, the git remote is a local file path by default. Let's change it to the upstream repo.
git remote set-url upstream https://github.com/frappe/crm.git

gh auth setup-git

# One stable branch, not a dated one. The POT file is fully regenerated every run, so a
# fresh dated branch/PR each week just piles up and conflicts once any one is merged. Reusing
# a single branch (reset to the base tip, force-pushed) keeps exactly one PR that updates in
# place and can never conflict, since it's always rebuilt from the current base.
branch_name="pot_${BASE_BRANCH}"

echo "Resetting ${branch_name} onto ${BASE_BRANCH}..."
generated_pot=$(mktemp)
cp crm/locale/main.pot "${generated_pot}"
git fetch upstream "${BASE_BRANCH}"
git checkout -f -B "${branch_name}" "upstream/${BASE_BRANCH}"
cp "${generated_pot}" crm/locale/main.pot

git add crm/locale/main.pot
if git diff --cached --quiet; then
  echo "No POT changes; nothing to do."
  exit 0
fi

echo "Commiting changes..."
git commit -m "chore: update POT file"

echo "Pushing ${branch_name}..."
git push -u upstream "${branch_name}" --force

if gh pr view "${branch_name}" -R frappe/crm --json state -q '.state' 2>/dev/null | grep -q OPEN; then
  echo "PR already open for ${branch_name}; force-push updated it."
else
  echo "Creating a PR..."
  gh pr create --fill --base "${BASE_BRANCH}" --head "${branch_name}" -R frappe/crm
fi
