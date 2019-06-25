
_dotdrop()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W '-h --help -v --version install import compare update remove listfiles detail list' -- $cur) )
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
            listfiles)
            _dotdrop_listfiles
        ;;
            detail)
            _dotdrop_detail
        ;;
            list)
            _dotdrop_list
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
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -c= --cfg= -p= --profile= -o= --dopts= -C= --file= -i= --ignore= ' -- $cur) )
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

_dotdrop_listfiles()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -T --template -c= --cfg= -p= --profile= ' -- $cur) )
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

_dotdrop_list()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -W '-V --verbose -b --no-banner -c= --cfg= ' -- $cur) )
    fi
}

complete -o bashdefault -o default -o filenames -F _dotdrop dotdrop