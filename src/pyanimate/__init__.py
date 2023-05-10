try:
    from rich.traceback import install

    install(show_locals=True)
except ImportError:
    pass
