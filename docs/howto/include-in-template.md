# Include file or template in template

[Jinja2](http://jinja.pocoo.org/docs/2.10/templates/) provides the ability to include an external file/template from within a template with the directive `include`. See the [related doc](http://jinja.pocoo.org/docs/2.10/templates/#include) for more. The path must be relative to the `dotpath`.

For example:
```yaml
{%@@ include 'colors/black.colors' @@%}
```

Of course, paths could be also dynamically generated using variables.
For example:
```yaml
{%@@ include colors_path + '/black.colors' @@%}
```
