# Handle special chars

* [Detect encoding](#detect-encoding)
* [Special chars](#special-chars)
* [Re-encode](#re-encode)

---

## Detect encoding

Text file encoding can be identified using, for example, `file -b <file-path>` or in vim
with `:set fileencoding`.

Here's an example of encoding that will fully work with dotdrop:
```bash
$ file -b <some-file>
UTF-8 Unicode text, with escape sequences
```

and another that will mislead the `compare` command and return false/inaccurate results:
```bash
$ file -b <some-file>
ISO-8859 text, with escape sequences
```

## Special chars

### CRLF

The use of dotfiles with DOS/Windows line endings (CRLF, `\r\n`) will result in
the comparison (`compare`) returning a difference where there is none.
This is due to Jinja2 stripping CRLF.

One solution is to use `dos2unix` to re-format the dotfiles before adding them
to dotdrop.

See <https://github.com/deadc0de6/dotdrop/issues/42>.

### Non-Unicode chars

Jinja2 is not able to process non-Unicode chars (<https://jinja.palletsprojects.com/en/2.11.x/api/>). This means that dotfiles using non-Unicode chars can still be fully managed by dotdrop; however, when comparing the local file with the one stored in dotdrop, `compare` will return a difference even if there is none.

Either replace the non-Unicode chars (see below [Re-encode](#re-encode)) or accept the fact the comparison shows a difference while there's none.

See <https://github.com/deadc0de6/dotdrop/issues/42>.

## Re-encode

To change an existing file's encoding, you can use `recode UTF-8 <filename>` (see [recode](https://linux.die.net/man/1/recode)) or in vim `:set fileencoding=utf-8`.
