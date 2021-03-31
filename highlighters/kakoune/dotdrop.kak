hook global WinCreate .* %{
    require-module python
    add-highlighter window/dotdrop regions

    add-highlighter window/dotdrop/expression region '\{\{@[@]' '[@]@\}\}' group
    add-highlighter window/dotdrop/statement  region  '\{%@[@]' '[@]@%\}' group
    add-highlighter window/dotdrop/comment    region  '\{#@[@]' '[@]@#\}' fill comment

    add-highlighter window/dotdrop/expression/ fill variable
    add-highlighter window/dotdrop/statement/  fill variable

    add-highlighter window/dotdrop/expression/ ref python
    add-highlighter window/dotdrop/statement/  ref python

    add-highlighter window/dotdrop/expression/ regex '\{\{@[@]|[@]@\}\}' 0:block
    add-highlighter window/dotdrop/statement/  regex  '\{%@[@]|[@]@%\}' 0:block
    add-highlighter window/dotdrop/statement/  regex 'endfor|endif' 0:keyword
}
