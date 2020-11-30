#!/usr/bin/env bash

echo "$(date) %%%%%%%%%%%%%%%%%%%%%% Start syncing. %%%%%%%%%%%%%%%%%%%%%%"
source /etc/profile
echo "$(date) Current branch:$APP_BRANCH"

function update_application() {
  echo ""
  echo "$(date) Start checking out $1"
  cd $1 || exit 125
  sudo chown ubuntu. .git/* -R
  echo "$(date) Change ownership $1/.git/"
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
  git log -1
  echo "$(date) Updated $1"
  sudo chown ubuntu. .git/* -R
  sudo chown ubuntu. * -R
}

update_application "/home/ubuntu/projects/python/misc/sqs_workflow"

echo "$(date) Start embedded sync"
bash /home/ubuntu/projects/grails/ui-horizon-net/aids/tomcat/embedded-sync.sh
echo "$(date) Finished embedded sync"

echo "$(date) Start cleaning up"
bash /home/ubuntu/projects/grails/ui-horizon-net/aids/tomcat/prepare-for-deployment.sh
echo "$(date) Finished cleaning up"

update_application "/home/ubuntu/projects/python/layout-validation"
update_application "/home/ubuntu/projects/python/ai-research"
update_application "/home/ubuntu/projects/python/ai-object-recognition"

image_name="ai-$APP_BRANCH-$(date '+%Y-%m-%d-%H-%M')"
aws --profile clipnow ec2 create-image --instance-id $(ec2metadata --instance-id) \
  --description $image_name \
  --name $image_name \
  --no-reboot \
  --region "eu-west-1"

echo "$(date) Image is created"

echo "$(date) %%%%%%%%%%%%%%%%%%%%%% Finished sync for reboot %%%%%%%%%%%%%%%%%%%%%%"
