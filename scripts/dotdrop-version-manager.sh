#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6

api="https://api.github.com/repos"
pro="deadc0de6/dotdrop"

# get current status
get_current()
{
  tag=`git describe --tags 2>/dev/null`
  branch=`git branch --show-current 2>/dev/null`
  [ "$tag" != "" ] && echo "tag: ${tag}"
  [ "$branch" != "" ] && echo "branch: ${branch}"
}

# get latest release
get_latest()
{
  curl "${api}/${pro}/releases/latest" 2>/dev/null | grep 'tag_name' | sed 's/^.*: "\(.*\)",/\1/g'
}

# list all releases
get_releases()
{
  curl "${api}/${pro}/releases" 2>/dev/null | grep 'tag_name' | sed 's/^.*: "\(.*\)",/\1/g'
}

# list all branches
get_branches()
{
  curl "${api}/${pro}/branches" 2>/dev/null | grep name | sed 's/^.*: "\(.*\)",/\1/g'
}

# print usage
usage()
{
  echo "${0} current:              current version tracked"
  echo "${0} releases:             list all releases"
  echo "${0} branches:             list all branches"
  echo "${0} get latest:           get latest stable release"
  echo "${0} get master:           get master branch"
  echo "${0} get <version>:        get a specific version"
  echo "${0} get branch <branch>:  get a specific version"
}

[ "$1" = "" ] && usage && exit 1
[ "$1" != "current" ] && [ "$1" != "releases" ] && [ "$1" != "get" ] && [ "$1" != "branches" ] && usage && exit 1
[ "$1" = "get" ] && [ "$2" = "" ] && usage && exit 1
[ "$1" = "get" ] && [ "$2" = "branch" ] && [ "$3" = "" ] && usage && exit 1

curpwd=`pwd`
cd dotdrop

if [ "$1" = "current" ]; then
  get_current
elif [ "$1" = "releases" ]; then
  get_releases
elif [ "$1" = "branches" ]; then
  get_branches
elif [ "$1" = "get" ]; then
  if [ "$2" = "latest" ]; then
    last=$(get_latest)
    git fetch origin
    git checkout ${last}
  elif [ "$2" = "master" ]; then
    git fetch origin
    git checkout master
    git pull
  elif [ "$2" = "branch" ]; then
    git fetch origin
    git checkout ${3}
    git pull origin ${3}
  else
    git fetch origin
    git checkout ${2}
  fi
fi

cd ${curpwd}

exit 0
