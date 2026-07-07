import signal
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_signal() -> Generator[MagicMock]:
    # Make sure we mock the signal module so interrupts work normally when running
    # the test suite via pytest
    with patch.object(signal, "signal") as mock:
        yield mock
