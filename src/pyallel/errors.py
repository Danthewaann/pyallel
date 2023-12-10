class InvalidExecutableError(Exception):
    def __init__(self, exe: str) -> None:
        super().__init__(exe)
        self.exe = exe


class InvalidExecutableErrors(Exception):
    def __init__(self, *errors: InvalidExecutableError) -> None:
        super().__init__(
            f"executables [{', '.join(error.exe for error in errors)}] were not found"
        )
