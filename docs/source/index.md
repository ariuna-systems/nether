# Nether

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

    def on_start(self) -> None:
        print(f"Start {self.__class__.__name__}")
    
    def on_stop(self) -> None:
        print(f"Stop {self.__class__.__name__}")
```

The app will be running until you stop it by pressing `Ctrl + C`.

### Components

Nether framework is build in a modular fashion. It is based on components. Component can be registere on application and can expose a views to the user. Each view has a route through which it can be accessed.

Example: Account component expose REST API on  `/api/account/` and UI on `/account/` route.

```{toctree}
:maxdepth: 2
:caption: Contents:

architecture-review
api
```
