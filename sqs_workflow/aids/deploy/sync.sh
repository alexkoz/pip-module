#!/usr/bin/env bash

function update_application() {
  echo ""
  echo "$(date) Start checking out $1"
  cd $1 || exit 125
  sudo chown ubuntu. .git/* -R
  echo "$(date) Change ownership $1.git/"
  git checkout "$APP_BRANCH"
  git pull --rebase
  pull_output=$(git pull --rebase)
  if [[ $pull_output != *" up to date."* ]]; then
    echo "Error updating $1!"
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"Failed Sync '"$1"' branch:'"$APP_BRANCH"'  <!channel>"}' \
      "$SLACK_URL"
    echo "Sent slack notification"
    exit 125
  fi
  sudo chown ubuntu. .git/* -R
  sudo chown ubuntu. * -R
  git log -1

  echo "$(date) Updated $1"
}

echo "$(date) %%%%%%%%%%%%%%%%%%%%%% Start syncing. %%%%%%%%%%%%%%%%%%%%%%"

echo "$(date) Current branch:$APP_BRANCH"

update_application "/home/ubuntu/projects/python/misc/sqs_workflow/"

update_application "/home/ubuntu/projects/python/layout-validation/"
update_application "/home/ubuntu/projects/python/ai-research"

echo "$(date) %%%%%%%%%%%%%%%%%%%%%% Finished sync for reboot %%%%%%%%%%%%%%%%%%%%%%"
