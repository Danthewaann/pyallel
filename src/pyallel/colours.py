from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Literal

from pyallel import constants


@dataclass
class Colours:
    white_bold: str = "\033[1m"
    green_bold: str = "\033[1;32m"
    blue_bold: str = "\033[1;34m"
    red_bold: str = "\033[1;31m"
    yellow_bold: str = "\033[1;33m"
    reset_colour: str = "\033[0m"
    dim_on: str = "\033[2m"
    dim_off: str = "\033[22m"

    @classmethod
    def from_colour(cls, colour: Literal["yes", "no", "auto"]) -> Colours:
        colours = cls()

        if colour == "no" or colour == "auto" and not constants.IN_TTY:
            for field in fields(colours):
                setattr(colours, field.name, "")

        return colours
