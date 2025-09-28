class Sandbox:
    """
    Sandbox for runing an actor in isolated  environment.
    """

    def __init__(self, id, name, machine) -> None:
        self.id = id
        self.name = name
        self.machine = machine
