"""Wrapper launcher that runs the package module as __main__ to preserve package-relative imports."""
if __name__ == '__main__':
    try:
        # Static import ensures PyInstaller includes the package and avoids runpy warnings
        from itech_interface import main as _main
        # `main` may be a module with a `main()` function, or the callable itself
        if callable(_main):
            _main()
        elif hasattr(_main, 'main'):
            _main.main()
        else:
            raise RuntimeError('Entry point `itech_interface.main` is neither callable nor module with main()')
    except Exception:
        import traceback, sys
        traceback.print_exc()
        sys.exit(1)
