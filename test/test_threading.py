import traceback
import threading
from testhelpers import create_dummy_entrypoint, get_nsdk

def thread_worker(err, sdk):
    try:
        with create_dummy_entrypoint(sdk):
            pass
    except Exception: #pylint:disable=broad-except
        err.append(traceback.format_exc())



def test_threading(sdk):
    """Regression test for bug where the paththread local was only created on
    the thread where the constructor of the mock sdk was called."""
    err = []
    thread = threading.Thread(
        target=thread_worker,
        args=(err, sdk))
    thread.start()
    with create_dummy_entrypoint(sdk):
        pass
    thread.join()
    if err:
        raise RuntimeError('Exception on ' + thread.name + ': ' + err[0])

    assert len(get_nsdk(sdk).finished_paths) == 2
