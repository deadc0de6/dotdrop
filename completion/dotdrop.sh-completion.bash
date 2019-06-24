
_dotdropsh()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W '-h --help -v --version install import compare update remove listfiles detail list' -- $cur) )
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
            listfiles)
            _dotdropsh_listfiles
        ;;
            detail)
            _dotdropsh_detail
        ;;
            list)
            _dotdropsh_list
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
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -c= --cfg= -p= --profile= -o= --dopts= -C= --file= -i= --ignore= ' -- $cur) )
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

_dotdropsh_listfiles()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -T --template -c= --cfg= -p= --profile= ' -- $cur) )
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

_dotdropsh_list()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -c= --cfg= ' -- $cur) )
    fi
}

complete -o bashdefault -o default -o filenames -F _dotdropsh dotdrop.sh