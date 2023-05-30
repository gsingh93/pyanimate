import inspect
import logging
import os

try:
    from rich.traceback import install

    install(show_locals=True)
except ImportError:
    pass

VERBOSE = logging.DEBUG - 5
logging.VERBOSE = VERBOSE  # type: ignore[attr-defined]


class IndentFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_depth = None

    def format(self, rec: logging.LogRecord) -> str:
        stack: list[inspect.FrameInfo] = inspect.stack()

        # We need to skip 8 stack frames of the logging infrastructure to get to the
        # real stack frame
        frame = stack[8]

        # We assume that the first time we call the logger we are at the base depth
        # TODO: Is there a more robust way to do this?
        if self.base_depth is None:
            # We want the indent to be 1 for the first call, so if `base_depth` is set
            # as below, then the indent is `len(stack) - 8 - (len(stack) - 8 - 1) = 1`
            self.base_depth = len(stack) - 8 - 1

        rec.indent = " " * (len(stack) - 8 - self.base_depth)
        rec.funcName = frame.function
        out = logging.Formatter.format(self, rec)
        first, *rest = out.split("]")
        first, second = first.split(" - ")
        second = second.rjust(20)
        out = first + " - " + second + "]" + "]".join(rest)
        del rec.indent  # pyright: ignore[reportGeneralTypeIssues]
        return out


class AlignFormatter(logging.Formatter):
    def format(self, rec: logging.LogRecord) -> str:
        stack: list[inspect.FrameInfo] = inspect.stack()
        # We need to skip 8 stack frames of the logging infrastructure to get to the
        # real stack frame
        frame = stack[8]

        # TODO: Also need to update filename
        rec.funcName = frame.function
        out = logging.Formatter.format(self, rec)
        first, *rest = out.split("]")
        first, second = first.split(" - ")
        second = second.rjust(20)
        out = first + " - " + second + "]" + "]".join(rest)
        return out


class CustomLogger(logging.getLoggerClass()):
    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(name, level)

        self.propagate = False

        logging.addLevelName(VERBOSE, "VERBOSE")

    def verbose(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kwargs)


logging.setLoggerClass(CustomLogger)


def get_logger(name: str, *, indent: bool = False) -> CustomLogger:
    log_level = os.getenv("PYANIMATE_LOG_LEVEL", None)

    if log_level and log_level.upper() not in logging.getLevelNamesMapping():
        params = log_level.split(",")
        level = None
        for p in params:
            module_name, level = p.split("=")

            module_name = "pyanimate." + module_name
            level = level.upper()
            if module_name == name:
                assert level in logging.getLevelNamesMapping()
                break

            level = None

        log_level = level

    logger = logging.getLogger(name)
    if log_level is not None:
        logger.setLevel(log_level)

    # TODO: The docs say that libraries shouldn't add handlers to their loggers, and
    # that should only be done by applications. But I don't know how to do this and
    # still allow the use of the IndentFormatter.
    if indent:
        formatter = IndentFormatter(
            "[{levelname:7} - {filename}:{lineno}] {indent}{funcName}(): {message}",
            style="{",
        )
    else:
        formatter = AlignFormatter(
            "[{levelname:7} - {filename}:{lineno}] {funcName}(): {message}",
            style="{",
        )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger  # type: ignore
