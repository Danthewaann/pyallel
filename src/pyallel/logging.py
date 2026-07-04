import logging
import os


def configure_logging(*, debug: bool = False) -> None:
    if debug:
        logging.basicConfig(
            filename="pyallel.log",
            format="%(asctime)s:%(name)s:%(lineno)d:%(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(handlers=[logging.StreamHandler(stream=open(os.devnull, "w"))])  # noqa: PTH123, SIM115
