Here are the completion files for `bash`, `zsh` and `fish`.
for the use of dotdrop either through the bash script `dotdrop.sh`
or through the python script `dotdrop` (pypi, snap, setup.py, etc).

`bash` and `zsh` scripts are generated using
[infi.docopt_completion](https://github.com/Infinidat/infi.docopt_completion).

# bash

Source the file

* if using `dotdrop.sh` [dotdrop.sh-completion.bash](dotdrop.sh-completion.bash)
* if using `dotdrop`: [dotdrop-completion.bash](dotdrop-completion.bash)

# zsh

Copy the file in a path within `${fpath}`

* if using `dotdrop.sh`: [_dotdrop.sh-completion.zsh](_dotdrop.sh-completion.zsh)
* if using `dotdrop`: [_dotdrop-completion.zsh](_dotdrop-completion.zsh)

# fish

Install for your user:
```bash
mkdir -p ~/.config/fish/completions
cp dotdrop.fish ~/.config/fish/completions/
```

Install system-wide:
```bash
cp dotdrop.fish /usr/share/fish/completions/
```
