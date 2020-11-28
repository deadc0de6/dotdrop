#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6

api="https://api.github.com/repos"
pro="deadc0de6/dotdrop"

git_get_changes()
{
  #git fetch origin
  git remote update
}

# get current status
get_current()
{
  tag=$(get_current_tag)
  [ "$tag" != "" ] && echo "tag: ${tag}"
  branch=$(get_current_branch)
  [ "$branch" != "" ] && echo "branch: ${branch}"
}

# get current tag
get_current_tag()
{
  git describe --tags --long 2>/dev/null
}

get_current_branch()
{
  git branch --show-current 2>/dev/null
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

need_update()
{
  git fetch origin >/dev/null 2>&1
  last=$(get_latest)
  cur=$(get_current_tag)
  # get short tag if on a lightweight tag
  echo "you are on ${cur}"
  tag=$(echo "$cur" | sed 's/\(v.*\)-.-.*$/\1/g')
  #nb=$(echo "$cur" | sed 's/v.*-\(.\)-.*$/\1/g')
  #commit=$(echo "$cur" | sed 's/v.*-.-\(.*\)$/\1/g')
  # compare
  if [ "${tag}" != "${last}" ]; then
    echo "new version available: ${last}" && return
  fi
  changes=$(git status -s)
  [ "${changes}" != "" ] && echo "new updates available" && return
  echo "your version is up-to-date"
}

checkout_last_tag()
{
  last=$(get_latest)
  [ "${last}" = "" ] && echo "unable to get last release" && return
  cur=$(get_current_tag)
  [ "${cur}" = "${last}" ] && return
  git_get_changes && git checkout "${last}"
}

# $1: tag
checkout_tag()
{
  cur=$(get_current_tag)
  [ "${cur}" = "${1}" ] && return
  git_get_changes && git checkout "${1}"
}

checkout_branch()
{
  git_get_changes && git checkout "${1}" && git pull origin "${1}"
}

# move to base of dotdrop
move_to_base()
{
  curpwd=$(pwd)
  git submodule | grep dotdrop >/dev/null 2>&1
  if [ "$?" ]; then
    # dotdrop is a submodule
    echo "dotdrop used as a submodule"
    cd dotdrop || (echo "cannot change directory to dotdrop" && exit 1)
    return
  fi

  if [ -e dotdrop/version.py ]; then
    grep deadc0de6 dotdrop/version.py >/dev/null 2>&1
    if [ "$?" ]; then
      # dotdrop is in current dir
      echo "dotdrop is in current directory"
      return
    fi
  fi

  echo "dotdrop wasn't found"
  exit 1
}

# print usage
usage()
{
  echo "$(basename "${0}") current              : current version tracked"
  echo "$(basename "${0}") releases             : list all releases"
  echo "$(basename "${0}") branches             : list all branches"
  echo "$(basename "${0}") check                : check for updates"
  echo "$(basename "${0}") get latest           : get latest stable release"
  echo "$(basename "${0}") get master           : get master branch"
  echo "$(basename "${0}") get <version>        : get a specific version"
  echo "$(basename "${0}") get branch <branch>  : get a specific version"
}

[ "$1" = "" ] && usage && exit 1
[ "$1" != "current" ] && \
  [ "$1" != "releases" ] && \
  [ "$1" != "get" ] && \
  [ "$1" != "branches" ] && \
  [ "$1" != "check" ] && \
  usage && exit 1
[ "$1" = "get" ] && [ "$2" = "" ] && usage && exit 1
[ "$1" = "get" ] && [ "$2" = "branch" ] && [ "$3" = "" ] && usage && exit 1

move_to_base

if [ "$1" = "current" ]; then
  get_current
elif [ "$1" = "releases" ]; then
  get_releases
elif [ "$1" = "branches" ]; then
  get_branches
elif [ "$1" = "check" ]; then
  need_update
elif [ "$1" = "get" ]; then
  if [ "$2" = "latest" ]; then
    checkout_last_tag
  elif [ "$2" = "master" ]; then
    checkout_branch master
  elif [ "$2" = "branch" ]; then
    checkout_branch "${3}"
  else
    checkout_tag "${2}"
  fi
fi

cd "${curpwd}" || true

exit 0
