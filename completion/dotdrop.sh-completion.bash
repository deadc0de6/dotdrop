
_dotdropsh()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W '-h --help -v --version install import compare update remove files detail profiles' -- $cur) )
    else
        case ${COMP_WORDS[1]} in
            install)
            _dotdropsh_install
        ;;
            import)
            _dotdropsh_import
        ;;
            compare)
            _dotdropsh_compare
        ;;
            update)
            _dotdropsh_update
        ;;
            remove)
            _dotdropsh_remove
        ;;
            files)
            _dotdropsh_files
        ;;
            detail)
            _dotdropsh_detail
        ;;
            profiles)
            _dotdropsh_profiles
        ;;
        esac

    fi
}

_dotdropsh_install()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -t --temp -f --force -n --nodiff -d --dry -D --showdiff -a --force-actions -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdropsh_import()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -d --dry -f --force -c= --cfg= -p= --profile= -l= --link= ' -- $cur) )
    fi
}

_dotdropsh_compare()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -c= --cfg= -p= --profile= -C= --file= -i= --ignore= ' -- $cur) )
    fi
}

_dotdropsh_update()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -f --force -d --dry -k --key -P --show-patch -c= --cfg= -p= --profile= -i= --ignore= ' -- $cur) )
    fi
}

_dotdropsh_remove()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -f --force -d --dry -k --key -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdropsh_files()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -T --template -G --grepable -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdropsh_detail()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-V --verbose -b --no-banner -c= --cfg= -p= --profile= ' -- $cur) )
    fi
}

_dotdropsh_profiles()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -G --grepable -c= --cfg= ' -- $cur) )
    fi
}

complete -o bashdefault -o default -o filenames -F _dotdropsh dotdrop.sh