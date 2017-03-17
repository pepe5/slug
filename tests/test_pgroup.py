import pytest
import os
import slug
from slug import ProcessGroup, Process, Pipe
from conftest import runpy


def test_group():
    with ProcessGroup() as pg:
        p1 = Pipe()
        pg.add(Process(runpy("print('spam')"), stdout=p1.side_in))
        p2 = Pipe()
        pg.add(Process(runpy("print('eggs')"), stdout=p2.side_in))
        p3 = Pipe()
        pg.add(Process(runpy("print('vikings')"), stdout=p3.side_in))

    pg.start()
    p1.side_in.close()
    p2.side_in.close()
    p3.side_in.close()
    pg.join()

    assert p1.side_out.read().rstrip() == b'spam'
    assert p2.side_out.read().rstrip() == b'eggs'
    assert p3.side_out.read().rstrip() == b'vikings'


def test_terminate():
    with ProcessGroup() as pg:
        pg.add(Process(runpy("input()")))
        pg.add(Process(runpy("input()")))
        pg.add(Process(runpy("input()")))

    pg.start()
    pg.terminate()
    pg.join()
    # Timing out is failure.


def test_kill():
    with ProcessGroup() as pg:
        pg.add(Process(runpy("input()")))
        pg.add(Process(runpy("input()")))
        pg.add(Process(runpy("input()")))

    pg.start()
    pg.kill()
    pg.join()
    # Timing out is failure.


@pytest.mark.skipif(not hasattr(ProcessGroup, 'pgid'),
                    reason="No Process Group IDs")
def test_pgid():
    with ProcessGroup() as pg:
        pg.add(Process(runpy("input()")))
        pg.add(Process(runpy("input()")))
        pg.add(Process(runpy("input()")))
    pg.start()
    assert pg.pgid is not None
    assert all(pg.pgid == p.pgid for p in pg)
    assert pg.pgid != os.getpgrp()
    pg.kill()


@pytest.mark.skipif(ProcessGroup is slug.base.ProcessGroup,
                    reason="Base Process Group is broken this way")
def test_kill_descendents():
    with ProcessGroup() as pg:
        pin = Pipe()
        pout = Pipe()
        pg.add(Process(
            runpy("""import subprocess
import sys
child = subprocess.Popen([sys.executable, '-c', '''
print("spam")
input()
print("eggs")
'''])
child.wait()
"""),
            stdin=pin.side_out,
            stdout=pout.side_in,
        ))
    pg.start()
    pin.side_out.close()
    pout.side_in.close()
    assert pout.side_out.read(4) == b'spam'
    pg.terminate()
    pg.join()
    try:
        pin.side_in.write(b'\n')
        pin.side_in.close()
    except BrokenPipeError:
        pass
    assert pout.side_out.read() in b'\r\n'