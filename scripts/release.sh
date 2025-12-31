#!/usr/bin/env bash
set -euo pipefail

# Release script:
# 1. Ensure working tree is clean
# 2. Push local commits to remote if any (set upstream if needed)
# 3. Bump patch version based on VERSION file (vMAJOR.MINOR.PATCH)
# 4. Run scripts/update_version.sh with new version
# 5. Commit VERSION and backend/app/__init__.py, push
# 6. Create git tag and push the tag

root_dir="$(git rev-parse --show-toplevel)"
cd "$root_dir"

echo "Repository root: $root_dir"

# ensure working tree is clean
if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree is not clean. Please commit or stash your changes before releasing."
  git status --porcelain
  exit 1
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $current_branch"

# fetch remote info
git fetch origin --prune

# ensure upstream exists or push and set upstream
if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  ahead_count=$(git rev-list --count @{u}..HEAD || echo 0)
  if [ "$ahead_count" -gt 0 ]; then
    echo "Found $ahead_count local commits ahead of upstream. Pushing..."
    git push
  else
    echo "No local commits to push."
  fi
else
  echo "No upstream configured for branch $current_branch. Pushing and setting upstream..."
  git push -u origin "$current_branch"
fi

# Read current version
if [ ! -f VERSION ]; then
  echo "VERSION file not found. Create a VERSION file with content like 'v1.2.3'"
  exit 1
fi

current_version=$(cat VERSION | tr -d ' \n' || true)
echo "Current version: $current_version"

if [[ "$current_version" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  major=${BASH_REMATCH[1]}
  minor=${BASH_REMATCH[2]}
  patch=${BASH_REMATCH[3]}
  new_patch=$((patch + 1))
  new_version="v${major}.${minor}.${new_patch}"
else
  echo "VERSION ($current_version) does not match expected format vMAJOR.MINOR.PATCH"
  exit 1
fi

echo "Bumping version -> $new_version"

# run update script
if [ ! -x "./scripts/update_version.sh" ]; then
  echo "Making update_version.sh executable"
  chmod +x ./scripts/update_version.sh || true
fi

./scripts/update_version.sh "$new_version"

echo "Staging VERSION and backend/app/__init__.py..."
git add VERSION backend/app/__init__.py

commit_msg="chore(release): bump version to ${new_version}"
git commit -m "$commit_msg" || {
  echo "No changes to commit (perhaps version was already updated)."
}

echo "Pushing commits..."
git push

echo "Creating and pushing tag ${new_version}..."
git tag "${new_version}"
git push origin "${new_version}"

echo "Release ${new_version} complete."


