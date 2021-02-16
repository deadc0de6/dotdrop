#!/usr/bin/env fish

# All available subcommands
#
set commands\
  install import  compare update\
  remove  files   detail  profiles

# Aliases to avoid walls of text
#
function __fish_dotdrop_comp_sub
    complete -f -c dotdrop\
        -n "not __fish_seen_subcommand_from $commands"\
        $argv
end
function __fish_dotdrop_comp_opt -a "command"
    complete -c dotdrop\
        -n "__fish_seen_subcommand_from $command"\
        $argv[2..-1]
end

function __fish_dotdrop_list_profiles
    dotdrop profiles \
        --grepable \
        --no-banner \
        2> /dev/null
end

function __fish_dotdrop_list_test_keys -a "test_arg"
    # Return only dotdrop keys in which the src field matches a test(1) criteria
    #        ^⌣ ^  ← "Slide Time!!"
    dotdrop files \
        --grepable \
        --no-banner \
        2> /dev/null |
    while read line
        # Single use variable because fish's output capture may change soon
        set -l dst (echo $line | cut -d, -f2 | cut -d: -f2 )
        if test $test_arg "$dst"
            echo $line
        end
    end |
    cut -d, -f1
end


# Complete subcommands
#
__fish_dotdrop_comp_sub  -k -a "profiles" -d "List available profiles"
__fish_dotdrop_comp_sub  -k -a "detail"   -d "List managed dotfiles details"
__fish_dotdrop_comp_sub  -k -a "files"    -d "List managed dotfiles"
__fish_dotdrop_comp_sub  -k -a "remove"   -d "Remove a managed dotfile"
__fish_dotdrop_comp_sub  -k -a "update"   -d "Update a managed dotfile"
__fish_dotdrop_comp_sub  -k -a "compare"  -d "Compare your local dotfiles with managed dotfiles"
__fish_dotdrop_comp_sub  -k -a "import"   -d "Import dotfiles into dotdrop"
__fish_dotdrop_comp_sub  -k -a "install"  -d "Install dotfiles"

# Lone options
#
__fish_dotdrop_comp_sub -s h -l help
__fish_dotdrop_comp_sub -s v -l version


# Common options to all subcommands
#
__fish_dotdrop_comp_opt "$commands"\
    -s V -l Verbose\
    -d "Show version"

__fish_dotdrop_comp_opt "$commands"\
    -s b -l no-banner\
    -d "Do not display the banner"

__fish_dotdrop_comp_opt "$commands"\
    -rF -s c -l cfg\
    -d "Path to the config"


# Subcommand specific options
#
__fish_dotdrop_comp_opt "install import update remove detail"\
    -s f -l force\
    -d "Do not ask user confirmation for anything"

__fish_dotdrop_comp_opt "install import  update remove"\
    -s d -l dry\
    -d "Dry run"

__fish_dotdrop_comp_opt "update remove"\
    -s k -l key\
    -d "Treat <path> as a dotfile key"

__fish_dotdrop_comp_opt "files"\
    -s T -l template\
    -d "Only template dotfiles"

__fish_dotdrop_comp_opt "install"\
    -s t -l temp\
    -d "Install to a temporary directory for review"

__fish_dotdrop_comp_opt "install"\
    -s n -l nodiff\
    -d "Do not diff when installing"

__fish_dotdrop_comp_opt "install"\
    -s D -l showdiff\
    -d "Show a diff before overwriting"

__fish_dotdrop_comp_opt "install"\
    -s a -l force-actions\
    -d "Execute all actions even if no dotfile is installed"

__fish_dotdrop_comp_opt "update"\
    -s P -l show-patch\
    -d "Provide a one-liner to manually patch template"

__fish_dotdrop_comp_opt "files profiles"\
    -s G -l grepable\
    -d "Grepable output"


# Command specific options with parameters
#

if test -z "$DOTDROP_PROFILE"
    set -l DOTDROP_PROFILE (uname -n)
end

__fish_dotdrop_comp_opt "install import compare update remove files detail"\
    -x -s p -l profile\
    -d "Specify the profile to use [default: $DOTDROP_PROFILE]"\
    -a "(__fish_dotdrop_list_profiles)"

__fish_dotdrop_comp_opt "compare update"\
    -x -s i -l ignore\
    -d "Pattern to ignore"

__fish_dotdrop_comp_opt "compare"\
    -rF -s C -l file\
    -d "Path of dotfile to compare"

__fish_dotdrop_comp_opt "import"\
    -rf -s l -l link\
    -a "nolink link link_children"\
    -d "Link option"

__fish_dotdrop_comp_opt "import"\
    -rF -s s -l as\
    -d "Import as a different path from actual path"


# Subcommand arguments
#
__fish_dotdrop_comp_opt "import"\
    -rF

__fish_dotdrop_comp_opt "update"\
    -F

__fish_dotdrop_comp_opt "remove"\
    -F

__fish_dotdrop_comp_opt "install detail"\
    -f\
    -d "File"\
    -a "(__fish_dotdrop_list_test_keys -f)"

__fish_dotdrop_comp_opt "install detail"\
    -f\
    -d "Directory"\
    -a "(__fish_dotdrop_list_test_keys -d)"

# dotdrop.sh
#
complete -c dotdrop.sh -w dotdrop

