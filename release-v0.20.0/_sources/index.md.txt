# Nether

Welcome to the Nether documentation!

Add your content using **Markdown** syntax. See the [MyST documentation](https://myst-parser.readthedocs.io/en/latest/) for details.

## Reference

### Application

Application class is a central point of your project which acts as an orchestrates and coordinator.
There should exactly one instance of an application when your process starts. You should inherit from  :class:nether.Applicaton`.

```python
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

The framework is designed with modularity at its core. Each part of the system is called a component, representing a distinct unit of functionality. Components can be thought of as the internal building blocks of the framework, responsible for specific features or services.

At the same time, components are designed to be extensible. This means they can also function as extensions—optional modules that can be added, replaced, or removed to customize or enhance the system’s capabilities. This dual nature allows developers to treat components both as essential internal parts and as plug-in extensions, similar to how modern modular platforms operate.

By following this approach, the framework supports both a robust core and flexible expansion, making it easy to adapt to new requirements or integrate third-party features.

Nether framework is build in a modular fashion. It is based on components. Component can be registere on application and can expose a views to the user. Each view has a route through which it can be accessed.

Example: Account component expose REST API on  `/api/account/` and UI on `/account/` route.

```{toctree}
:maxdepth: 2
:caption: Contents:

architecture-review
api
```
