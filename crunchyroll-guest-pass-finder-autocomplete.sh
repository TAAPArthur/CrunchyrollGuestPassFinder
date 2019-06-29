#!/bin/bash
_crunchyroll-guest-pass-finderAutocomplete()   #  By convention, the function name
{                 #+ starts with an underscore.
    local cur
    # Pointer to current completion word.
    # By convention, it's named "cur" but this isn't strictly necessary.

    options=" --auto -a --help -h --version -v --kill-time -k -u --username -p --password --config-dir --delay -d --driver --dry-run --graphical -g "

    COMPREPLY=() # Array variable storing the possible completions.
    cur=${COMP_WORDS[COMP_CWORD]}
    last=${COMP_WORDS[COMP_CWORD-1]}
    accountFile=~/.config/crunchyroll-guest-pass-finder/accounts.json

    if [[ COMP_CWORD -eq 1 ]]; then
        COMPREPLY=( $( compgen -W "$options " -- $cur ) )
    elif [[ -f $accountFile && ("$last" == "--username" || "$last" == "-u") ]]; then
        COMPREPLY=( $( compgen -W "$(jq '.[]| {u:.Username} |join("\n")' $accountFile  |sed 's/"//g') " -- $cur ) )
    else
        COMPREPLY=( $( compgen -W "$actions " -- $cur ) )
    fi
    return 0
}
complete -F _crunchyroll-guest-pass-finderAutocomplete crunchyroll-guest-pass-finder
