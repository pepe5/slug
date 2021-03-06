import pytest
import threading
import time
import slug
from slug import Valve, Pipe


def test_valve_through():
    pin = Pipe()
    pout = Pipe()
    v = Valve(
        side_in=pin.side_out,
        side_out=pout.side_in,
    )
    v.turn_on()

    pin.side_in.write(b'spameggs')
    pin.side_in.close()

    roundtrip = pout.side_out.read()
    assert roundtrip == b'spameggs'


def test_valve_stop():
    pin = Pipe()
    pout = Pipe()
    v = Valve(
        side_in=pin.side_out,
        side_out=pout.side_in,
    )

    pin.side_in.write(b'spameggs')
    pin.side_in.close()

    buf = None
    timediff = None

    def clockread():
        nonlocal buf, timediff
        s = time.perf_counter()
        buf = pout.side_out.read()
        e = time.perf_counter()
        timediff = e - s

    v.turn_off()
    t = threading.Thread(target=clockread, daemon=True)
    t.start()
    time.sleep(1.0)
    v.turn_on()
    t.join()

    assert buf == b'spameggs'
    assert timediff > 0.9


# Broken on windows, see https://github.com/xonsh/slug/issues/7
@pytest.mark.skipif(slug.Valve is slug.base.Valve,
                    reason="Base Valve is broken this way")
def test_valve_stop_midway():
    pin = Pipe()
    pout = Pipe()
    v = Valve(
        side_in=pin.side_out,
        side_out=pout.side_in,
    )

    v.turn_on()
    pin.side_in.write(b'spam')
    time.sleep(1.0)
    v.turn_off()
    pin.side_in.write(b'eggs')
    time.sleep(1.0)

    buf = pout.side_out.read(4000)

    assert buf == b'spam'
