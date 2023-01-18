# Improve Git integration

The below aliases can help with the process of updating your dotfiles between multiple hosts. Add them to your `~/.zshrc` or `~/.bashrc`. You can then simply run `dotsync` to push or pull from your dotfile repository.

```
# Your dotdrop git repository location
export DOTREPO="/path/to/your/dotdrop/repo"

alias dotdrop="$DOTREPO/dotdrop.sh"
alias dotgit="git -C $DOTREPO"
alias dotsync="dotgit pull && dotgit add -A && dotgit commit && dotgit push; dotdrop install"
```

Provided by ReekyMarko.
