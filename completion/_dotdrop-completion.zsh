#compdef dotdrop

_message_next_arg()
{
    argcount=0
    for word in "${words[@][2,-1]}"
    do
        if [[ $word != -* ]] ; then
            ((argcount++))
        fi
    done
    if [[ $argcount -le ${#myargs[@]} ]] ; then
        _message -r $myargs[$argcount]
        if [[ $myargs[$argcount] =~ ".*file.*" || $myargs[$argcount] =~ ".*path.*" ]] ; then
            _files
        fi
    fi
}

_dotdrop ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
		'(-h)-h[Show this screen.]' \
		'(--help)--help[Show this screen.]' \
		'(-v)-v[Show version.]' \
		'(--version)--version[Show version.]' \
        '*::options:->options'

    case $state in
        (command)
            local -a subcommands
            subcommands=(
				'install'
				'import'
				'compare'
				'update'
				'remove'
				'listfiles'
				'detail'
				'list'
            )
            _values 'dotdrop' $subcommands
        ;;

        (options)
            case $line[1] in
                install)
                    _dotdrop-install
                ;;
                import)
                    _dotdrop-import
                ;;
                compare)
                    _dotdrop-compare
                ;;
                update)
                    _dotdrop-update
                ;;
                remove)
                    _dotdrop-remove
                ;;
                listfiles)
                    _dotdrop-listfiles
                ;;
                detail)
                    _dotdrop-detail
                ;;
                list)
                    _dotdrop-list
                ;;
            esac
        ;;
    esac

}

_dotdrop-install ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-t)-t' \
		'(--temp)--temp' \
		'(-f)-f' \
		'(--force)--force' \
		'(-n)-n' \
		'(--nodiff)--nodiff' \
		'(-d)-d' \
		'(--dry)--dry' \
		'(-D)-D' \
		'(--showdiff)--showdiff' \
		'(-a)-a' \
		'(--force-actions)--force-actions' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \

    else
        myargs=('<key>')
        _message_next_arg
    fi
}

_dotdrop-import ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-d)-d' \
		'(--dry)--dry' \
		'(-f)-f' \
		'(--force)--force' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \
		'(-l=-)-l=-' \
		'(--link=-)--link=-' \

    else
        myargs=('<path>')
        _message_next_arg
    fi
}

_dotdrop-compare ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \
		'(-o=-)-o=-' \
		'(--dopts=-)--dopts=-' \
		'(-C=-)-C=-' \
		'(--file=-)--file=-' \
		'(-i=-)-i=-' \
		'(--ignore=-)--ignore=-' \
        
}

_dotdrop-update ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-f)-f' \
		'(--force)--force' \
		'(-d)-d' \
		'(--dry)--dry' \
		'(-k)-k' \
		'(--key)--key' \
		'(-P)-P' \
		'(--show-patch)--show-patch' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \
		'(-i=-)-i=-' \
		'(--ignore=-)--ignore=-' \

    else
        myargs=('<path>')
        _message_next_arg
    fi
}

_dotdrop-remove ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-f)-f' \
		'(--force)--force' \
		'(-d)-d' \
		'(--dry)--dry' \
		'(-k)-k' \
		'(--key)--key' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \

    else
        myargs=('<path>')
        _message_next_arg
    fi
}

_dotdrop-listfiles ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-T)-T' \
		'(--template)--template' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \
        
}

_dotdrop-detail ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
		'(-p=-)-p=-' \
		'(--profile=-)--profile=-' \

    else
        myargs=('<key>')
        _message_next_arg
    fi
}

_dotdrop-list ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
		'(-V)-V' \
		'(--verbose)--verbose' \
		'(-b)-b' \
		'(--no-banner)--no-banner' \
		'(-c=-)-c=-' \
		'(--cfg=-)--cfg=-' \
        
}


_dotdrop "$@"