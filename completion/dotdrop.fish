#!/usr/bin/env fish

# All available subcommands
#
set commands\
  install import  compare update\
  remove  files   detail  profiles

# Aliases to avoid walls of text
#
function comp_sub
    complete -f -c dotdrop\
        -n "not __fish_seen_subcommand_from $commands"\
        $argv
end
function comp_opt -a "command"
    complete -c dotdrop\
        -n "__fish_seen_subcommand_from $command"\
        $argv[2..-1]
end

function list_profiles
    dotdrop profiles \
        --grepable \
        --no-banner \
        2> /dev/null
end

function list_test_keys -a "test_arg"
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
comp_sub -a "install"  -d "Install dotfiles"
comp_sub -a "import"   -d "Import dotfiles into dotdrop"
comp_sub -a "compare"  -d "Compare your local dotfiles with managed dotfiles"
comp_sub -a "update"   -d "Update a managed dotfile"
comp_sub -a "remove"   -d "Remove a managed dotfile"
comp_sub -a "files"    -d "List managed dotfiles"
comp_sub -a "detail"   -d "List managed dotfiles details"
comp_sub -a "profiles" -d "List available profiles"

# Lone options
#
comp_sub -s h -l help
comp_sub -s v -l version


# Common options to all subcommands
#
comp_opt "$commands"\
    -s V -l Verbose\
    -d "Show version"

comp_opt "$commands"\
    -s b -l no-banner\
    -d "Do not display the banner"

comp_opt "$commands"\
    -rF -s c -l cfg\
    -d "Path to the config"


# Subcommand specific options
#
comp_opt "install import update remove detail"\
    -s f -l force\
    -d "Do not ask user confirmation for anything"

comp_opt "install import  update remove"\
    -s d -l dry\
    -d "Dry run"

comp_opt "update remove"\
    -s k -l key\
    -d "Treat <path> as a dotfile key"

comp_opt "files"\
    -s T -l template\
    -d "Only template dotfiles"

comp_opt "install"\
    -s t -l temp\
    -d "Install to a temporary directory for review"

comp_opt "install"\
    -s n -l nodiff\
    -d "Do not diff when installing"

comp_opt "install"\
    -s D -l showdiff\
    -d "Show a diff before overwriting"

comp_opt "install"\
    -s a -l force-actions\
    -d "Execute all actions even if no dotfile is installed"

comp_opt "update"\
    -s P -l show-patch\
    -d "Provide a one-liner to manually patch template"

comp_opt "files profiles"\
    -s G -l grepable\
    -d "Grepable output"


# Command specific options with parameters
#
comp_opt "install import compare update remove files detail"\
    -x -s p -l profile\
    -d "Specify the profile to use [default: "(uname -n)"]"\
    -a "(list_profiles)"

comp_opt "compare update"\
    -x -s i -l ignore\
    -d "Pattern to ignore"

comp_opt "compare"\
    -rF -s C -l file\
    -d "Path of dotfile to compare"

comp_opt "import"\
    -rf -s l -l link\
    -a "nolink link link_children"\
    -d "Link option"

comp_opt "import"\
    -rF -s s -l as\
    -d "Import as a different path from actual path"


# Subcommand arguments
#
comp_opt "import"\
    -rF

comp_opt "update"\
    -F

comp_opt "remove"\
    -F

comp_opt "install detail"\
    -f\
    -d "File"\
    -a "(list_test_keys -f)"

comp_opt "install detail"\
    -f\
    -d "Directory"\
    -a "(list_test_keys -d)"

# dotdrop.sh
#
complete -c dotdrop.sh -w dotdrop

