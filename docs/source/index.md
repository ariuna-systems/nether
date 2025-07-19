# Nether documentation

Welcome to the Nether documentation!

Add your content using **Markdown** syntax. See the [MyST documentation](https://myst-parser.readthedocs.io/en/latest/) for details.

## Reference

### Application

Application class is a central point of your project which acts as an orchestrates and coordinator.
There should exactly one instance of an application when your process starts. You should inherit from  :class:nether.Applicaton`.

```py
class Application(nether.Application):
    def __init__(self, ...) -> None:
        super().__init__(...)

    def on_start(self) -> None: ...
    def on_stop(self) -> None: ...

```

The app will be running until you stop it by pressing `Ctrl+C`.

```{toctree}
:maxdepth: 2
:caption: Contents:

architecture-review
api
```
