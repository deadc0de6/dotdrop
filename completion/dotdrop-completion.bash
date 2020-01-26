
_dotdrop()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W '-h --help -v --version install import compare update remove files detail profiles' -- $cur) )
    else
        case ${COMP_WORDS[1]} in
            install)
            _dotdrop_install
        ;;
            import)
            _dotdrop_import
        ;;
            compare)
            _dotdrop_compare
        ;;
            update)
            _dotdrop_update
        ;;
            remove)
            _dotdrop_remove
        ;;
            files)
            _dotdrop_files
        ;;
            detail)
            _dotdrop_detail
        ;;
            profiles)
            _dotdrop_profiles
        ;;
        esac

    fi
}

_dotdrop_install()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -t --temp -f --force -n --nodiff -d --dry -D --showdiff -a --force-actions -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdrop_import()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -d --dry -f --force -c= --cfg= -p= --profile= -l= --link= ' -- $cur) )
    fi
}

_dotdrop_compare()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -c= --cfg= -p= --profile= -C= --file= -i= --ignore= ' -- $cur) )
    fi
}

_dotdrop_update()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -f --force -d --dry -k --key -P --show-patch -c= --cfg= -p= --profile= -i= --ignore= ' -- $cur) )
    fi
}

_dotdrop_remove()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -f --force -d --dry -k --key -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdrop_files()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -T --template -G --grepable -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdrop_detail()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdrop_profiles()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -G --grepable -c= --cfg= ' -- $cur) )
    fi
}

complete -o bashdefault -o default -o filenames -F _dotdrop dotdrop