from __future__ import annotations

import pytest

from sam17.hardware.dac import DAC_MAX_VALUE, Dac


def test_send_writes_24_bit_frame(fake_spi):
    dac = Dac(fake_spi)
    dac.send(0x14, 0x1234)
    assert fake_spi.writes == [[0x14, 0x12, 0x34]]


def test_send_zero(fake_spi):
    dac = Dac(fake_spi)
    dac.send(0x18, 0)
    assert fake_spi.writes == [[0x18, 0x00, 0x00]]


def test_send_full_scale(fake_spi):
    dac = Dac(fake_spi)
    dac.send(0x11, DAC_MAX_VALUE)
    assert fake_spi.writes == [[0x11, 0xFF, 0xFF]]


@pytest.mark.parametrize("bad", [-1, DAC_MAX_VALUE + 1, 100_000])
def test_send_rejects_out_of_range(fake_spi, bad):
    dac = Dac(fake_spi)
    with pytest.raises(ValueError):
        dac.send(0x11, bad)
    assert fake_spi.writes == []


def test_close_propagates(fake_spi):
    dac = Dac(fake_spi)
    dac.close()
    assert fake_spi.closed is True
