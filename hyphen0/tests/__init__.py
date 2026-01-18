def run_all():
    from .test_zerotrust import run
    run()
    from .test_svclient import run
    run()