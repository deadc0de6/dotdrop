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


if test -z "$DOTDROP_PROFILE"
    set -l DOTDROP_PROFILE (uname -n)
end

# Short and Long options and their Descriptions
#
set -l  a -s a -l force-actions  -d "Execute all actions even if no dotfile is installed."
set -l  b -s b -l no-banner      -d "Do not display the banner."
set -l  c -s c -l cfg            -d "Path to the config."
set -l  C -s C -l file           -d "Path of dotfile to compare."
set -l  d -s d -l dry            -d "Dry run."
set -l  D -s D -l showdiff       -d "Show a diff before overwriting."
set -l  f -s f -l force          -d "Do not ask user confirmation for anything."
set -l  G -s G -l grepable       -d "Grepable output."
set -l  i -s i -l ignore         -d "Pattern to ignore."
set -l  k -s k -l key            -d "Treat <path> as a dotfile key."
set -l  l -s l -l link           -d "Link option (nolink|absolute|relative|link_children)."
set -l  L -s L -l file-only      -d "Do not show diff but only the files that differ."
set -l  m -s m -l preserve-mode  -d "Insert a chmod entry in the dotfile with its mode."
set -l  n -s n -l nodiff         -d "Do not diff when installing."
set -l  p -s p -l profile        -d "Specify the profile to use [default: $DOTDROP_PROFILE]."
set -l  P -s P -l show-patch     -d "Provide a one-liner to manually patch template."
set -l  s -s s -l as             -d "Import as a different path from actual path."
set -l  t -s t -l temp           -d "Install to a temporary directory for review."
set -l  T -s T -l template       -d "Only template dotfiles."
set -l  V -s V -l verbose        -d "Be verbose."
set -l  w -s w -l workers        -d "Number of concurrent workers [default: 1]."
set -l  v -s v -l version        -d "Show version."
set -l  h -s h -l help           -d "Show this screen."

# Configuration for arguments
#
set -al c -rF
set -al C -rF
set -al i -x
set -al l -x -a "nolink absolute relative link_children"
set -al p -x -a "(__fish_dotdrop_list_profiles)"
set -al s -rF
set -al w -x

# Parameters for main commands
#
set -l mustfile -rF
set -l nofile   -F
set -l nofile   -F
set -l files -d "File"       -a "(__fish_dotdrop_list_test_keys -f)"
set -l dirs  -d "Directory"  -a "(__fish_dotdrop_list_test_keys -d)"

# Column 1 represents to what subcommands thes following options will be applied
# Column 2 is a list which will be used for lookup from tables before
for line in "install:   V b t f n d D a c p w" \
            "import:    V b d f m c p s l" \
            "compare:   L V b c p w C i" \
            "update:    V b f d k P c p w i" \
            "remove:    V b f d k c p" \
            "files:     V b T G c p" \
            "detail:    V b c p" \
            "profiles:  V b G c" \
            "install:   files dirs" \
            "detail:    files dirs" \
            "import:    mustfile" \
            "update:    nofile" \
            "remove:    nofile" \
            # I'm here so no one is hurt by sharp backslashes

    set -l command (echo "$line" | cut -d: -f1 )

    for opt in (echo "$line" | cut -d: -f2 | string split -n ' ')
        complete -c dotdrop\
            -n "__fish_seen_subcommand_from $command" $$opt
    end
end


# dotdrop.sh
#
complete -c dotdrop.sh -w dotdrop

