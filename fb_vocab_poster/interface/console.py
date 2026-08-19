"""Terminal presentation. The only place in the codebase that prints."""


class ConsoleReporter:
    """Implements `application.ports.ProgressReporter`."""

    def step(self, message: str) -> None:
        print(message)

    def result(self, message: str) -> None:
        print(message)

    def notice(self, message: str) -> None:
        print(message)
