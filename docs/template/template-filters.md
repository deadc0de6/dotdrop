# Template filters

Besides [Jinja2 builtin filters](https://jinja.palletsprojects.com/en/2.11.x/templates/#builtin-filters),
custom user-defined filter functions can be loaded using the config entry `filter_file`:

Example:

The config file:
```yaml
config:
  filter_file:
  - /tmp/myfilter_file.py
```

The python filter under `/tmp/myfilter_file.py`:
```python
def myfilter(arg1):
  return str(int(arg1) - 10)
```

The dotfile content:
```
{{@@ "13" | myfilter() @@}}
```

For more information on how to create filters,
see [the Jinja2 official docs](https://jinja.palletsprojects.com/en/2.11.x/api/#writing-filters).