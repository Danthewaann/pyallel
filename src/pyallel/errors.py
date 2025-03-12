class PyallelError(Exception):
    """Base error for issues raised by pyallel"""


class InvalidLinesModifierError(PyallelError):
    """Raised when the lines modifier is invalid"""


class NoCommandsForProcessGroupError(PyallelError):
    """Raised when no commands have been provided for a process group"""
