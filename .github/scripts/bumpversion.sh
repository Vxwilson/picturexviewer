#!/bin/bash

# version follows the convention of semantic versioning x.y.z
# This script is used to bump the version of the project.
# get last tag
LAST_TAG=$(git describe --tags --abbrev=0)

# get the current version
CURRENT_VERSION=$(echo $LAST_TAG | cut -d'v' -f 2)

# get the commit message to know if it's a major, minor or patch
COMMIT_MESSAGE=$(git log -1 --pretty=%B)

# get the new version
if [[ $COMMIT_MESSAGE == *"BREAKING CHANGE"* ]]; then
  NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')
elif [[ $COMMIT_MESSAGE == *"feat"* ]]; then
  NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$2 = $2 + 1;} 1' | sed 's/ /./g')
else
  NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$3 = $3 + 1;} 1' | sed 's/ /./g')
fi
