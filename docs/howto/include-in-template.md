# Include file or template in template

[Jinja2](https://jinja.palletsprojects.com/en/2.11.x/templates/) provides the ability to include an external file/template from within a template with the directive `include`. See the [related doc](https://jinja.palletsprojects.com/en/2.11.x/templates/#include) for more. The path must be relative to the `dotpath`.

For example:
```yaml
{%@@ include 'colors/black.colors' @@%}
```

Of course, paths could be also dynamically generated using variables.
For example:
```yaml
{%@@ include colors_path + '/black.colors' @@%}
```
