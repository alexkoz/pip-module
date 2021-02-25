#!/usr/bin/env bash

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
  sudo chown ubuntu. .git/* -R
  sudo chown ubuntu. * -R
  git log -1

  echo "$(date) Updated $1"
}

echo "$(date) %%%%%%%%%%%%%%%%%%%%%% Start syncing. %%%%%%%%%%%%%%%%%%%%%%"

echo "$(date) Current branch:$APP_BRANCH"

update_application "/home/ubuntu/projects/python/misc/sqs_workflow"

update_application "/home/ubuntu/projects/python/layout-validation"
update_application "/home/ubuntu/projects/python/ai-research"
update_application "/home/ubuntu/projects/python/ai-object-recognition"
update_application "/home/ubuntu/projects/python/panorama-lineout"

echo "$(date '+%Y-%m-%d %H:%M:%S') Start updating wizard."

remove_wizard="sudo rm -rf /var/www/html/* "

eval $remove_wizard

wizard_command="aws --profile clipnow s3 cp s3://ai-process-$APP_BRANCH/wizard  /var/www/html/  --recursive"
echo $wizard_command
eval $wizard_command
echo "$(date '+%Y-%m-%d %H:%M:%S') Wizard uploaded."

ec2_data=$(ec2metadata --public-ipv4 --instance-id --ami-id)
echo "$(date '+%Y-%m-%d %H:%M:%S') Send slack notification for $ec2_data"

message_body='{"text":"Ai sqs consumer launched.'
message_body="$message_body $ec2_data Branch:$APP_BRANCH "
message_body=$message_body' "}'

#
curl -X POST -H 'Content-type: application/json' \
  --data "$message_body" \
  "$SLACK_URL"
echo "Sent slack notification"

echo "$(date) %%%%%%%%%%%%%%%%%%%%%% Finished sync for reboot %%%%%%%%%%%%%%%%%%%%%%"
