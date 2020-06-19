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

# Complete subcommands
#
comp_sub -a "install"  -d "Install from dotfiles"
comp_sub -a "import"   -d "Import from the filesystem into dotdrop"
comp_sub -a "compare"  -d "Compare local dotfiles with dotdrop"
comp_sub -a "update"   -d "Update from dotfiles into filesystem"
comp_sub -a "remove"   -d "Remove a file from the filesystem"
comp_sub -a "files"    -d "List files managed by dotdrop"
comp_sub -a "detail"   -d "Details of the selected profile"
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
    -d "Specify the profile to use [default: "(uname -n)"]" 

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

# TODO: complete keys
comp_opt "install"\
    -f

comp_opt "detail"\
    -f

# dotdrop.sh
#
complete -c dotdrop.sh -w dotdrop

