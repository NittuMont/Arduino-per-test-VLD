"""Wrapper launcher that runs the package module as __main__ to preserve package-relative imports."""
if __name__ == '__main__':
    try:
        from itech_interface.main import main
        main()
    except Exception:
        import traceback, sys
        traceback.print_exc()
        sys.exit(1)
