Here are completion files for `bash`, `zsh` and `fish`
for the use of dotdrop through the bash script `dotdrop.sh`
or through the Python script `dotdrop` (PyPI, snap, setup.py, etc.).

`bash` and `zsh` scripts are generated using
[infi.docopt_completion](https://github.com/Infinidat/infi.docopt_completion).

# bash

Source the file

* if using `dotdrop.sh`: [dotdrop.sh-completion.bash](dotdrop.sh-completion.bash)
* If using `dotdrop`: [dotdrop-completion.bash](dotdrop-completion.bash)

# zsh

Copy the file to a path within `${fpath}`

* If using `dotdrop.sh`: [_dotdrop.sh-completion.zsh](_dotdrop.sh-completion.zsh)
* If using `dotdrop`: [_dotdrop-completion.zsh](_dotdrop-completion.zsh)

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
