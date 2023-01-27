#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6

api="https://api.github.com/repos"
pro="deadc0de6/dotdrop"
logs="/tmp/dotdrop-version.log"

########################
## git operations
########################

git_get_changes()
{
  #git fetch origin
  git remote update >>${logs} 2>&1
}

get_current_commit()
{
  git rev-parse --short HEAD
}

# get current tag
get_current_tag()
{
  git describe --tags 2>/dev/null
}

get_current_branch()
{
  git branch --show-current 2>/dev/null
}

is_on_release()
{
  git describe --exact-match --tags HEAD >>${logs} 2>&1
  echo "$?"
}

checkout()
{
  git checkout "$1" >>${logs} 2>&1
}

########################
## api operations
########################

# get latest release
get_latest()
{
  curl "${api}/${pro}/releases/latest" 2>>${logs} | grep 'tag_name' | sed 's/^.*: "\(.*\)",/\1/g'
}

# list all releases
get_releases()
{
  curl "${api}/${pro}/releases" 2>>${logs} | grep 'tag_name' | sed 's/^.*: "\(.*\)",/\1/g'
}

# list all branches
get_branches()
{
  curl "${api}/${pro}/branches" 2>>${logs} | grep name | sed 's/^.*: "\(.*\)",/\1/g'
}

########################
## print status
########################

# get current status
get_current()
{
  local tag
  local commit
  local branch
  echo "current version:"
  stable=$(is_on_release)
  if [ "${stable}" = "0" ]; then
    echo -e "\ton stable"
    tag=$(get_current_tag)
    echo -e "\trelease version: ${tag}"
  else
    echo -e "\ton unstable"
    tag=$(get_current_tag)
    echo -e "\ttag: ${tag}"
    commit=$(get_current_commit)
    echo -e "\tcommit: ${commit}"
  fi

  branch=$(get_current_branch)
  [ "$branch" != "" ] && echo -e "\tbranch: ${branch}"
}


# check if new stable release is available
need_update_stable()
{
  local last
  local cur
  local tag
  git fetch origin >>${logs} 2>&1
  last=$(get_latest)
  cur=$(get_current_tag)
  # get short tag if on a lightweight tag
  # shellcheck disable=SC2001
  tag=$(echo "$cur" | sed 's/\(v.*\)-[0-9]*.-.*$/\1/g')
  if [ "${tag}" != "${last}" ]; then
    echo "new stable version available: ${last}" && exit 1
  fi
  echo "your version is up-to-date"
}

# check if new updates are available
need_update()
{
  local changes
  git fetch origin >>${logs} 2>&1

  # compare
  changes=$(git log HEAD..origin --oneline)
  [ "${changes}" != "" ] && echo "new updates available" && exit 1
  echo "your version is up-to-date"
}

########################
## change operations
########################

checkout_last_tag()
{
  local last
  local cur
  last=$(get_latest)
  [ "${last}" = "" ] && echo "unable to get last release" && return
  cur=$(get_current_tag)
  [ "${cur}" = "${last}" ] && return
  git_get_changes && checkout "${last}"
}

# $1: tag
checkout_tag()
{
  local cur
  cur=$(get_current_tag)
  [ "${cur}" = "${1}" ] && return
  git_get_changes && checkout "${1}"
}

checkout_branch()
{
  git_get_changes && checkout "${1}" && git pull origin "${1}" >/dev/null 2>&1
}

########################
## helpers
########################

# move to base of dotdrop
move_to_base()
{
  local curpwd
  curpwd=$(pwd)
  git submodule | grep dotdrop >/dev/null 2>&1
  if [ "$?" ]; then
    # dotdrop is a submodule
    #echo "dotdrop used as a submodule"
    cd dotdrop || (echo "cannot change directory to dotdrop" && exit 1)
    return
  fi

  if [ -e dotdrop/version.py ]; then
    grep deadc0de6 dotdrop/version.py >/dev/null 2>&1
    if [ "$?" ]; then
      # dotdrop is in current dir
      #echo "dotdrop is in current directory"
      return
    fi
  fi

  echo "dotdrop wasn't found"
  exit 1
}

# print usage
usage()
{
  echo "$(basename "${0}") print current           : print the version you are on"
  echo "$(basename "${0}") print releases          : list available stable releases"
  echo "$(basename "${0}") print branches          : list available branches"
  echo "$(basename "${0}") check unstable          : check for new unstable updates"
  echo "$(basename "${0}") check stable            : check for new stable release"
  echo "$(basename "${0}") get stable              : change to latest stable release"
  echo "$(basename "${0}") get unstable            : change to latest unstable"
  echo "$(basename "${0}") get version <version>   : change to a specific version"
  echo "$(basename "${0}") get branch <branch>     : change to a specific branch"
  exit 1
}

########################
## entry point
########################

[ "$1" = "" ] && usage
[ "$1" != "print" ] && \
  [ "$1" != "check" ] && \
  [ "$1" != "get" ] && \
  usage
[ "$2" = "" ] && usage

move_to_base

if [ "$1" = "print" ]; then
  if [ "$2" = "current" ]; then
    get_current
  elif [ "$2" = "releases" ]; then
    get_releases
  elif [ "$2" = "branches" ]; then
    get_branches
  else
    usage
  fi
elif [ "$1" = "check" ]; then
  if [ "$2" = "stable" ]; then
    get_current
    need_update_stable
  elif [ "$2" = "unstable" ]; then
    get_current
    need_update
  else
    usage
  fi
elif [ "$1" = "get" ]; then
  if [ "$2" = "stable" ]; then
    checkout_last_tag
    get_current
  elif [ "$2" = "unstable" ]; then
    checkout_branch master
    get_current
  elif [ "$2" = "branch" ]; then
    [ "$3" = "" ] && usage
    checkout_branch "${3}"
    get_current
  elif [ "$2" = "version" ]; then
    [ "$3" = "" ] && usage
    checkout_tag "${3}"
    get_current
  else
    usage
  fi
fi

cd "${curpwd}" || true

exit 0
