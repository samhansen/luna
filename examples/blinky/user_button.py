#!/usr/bin/env python3
#
# This file is part of LUNA.
#
# Copyright (c) 2026 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2026 Sam Hansen <hansensc82@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

""" Sample gateware applet demonstrating button debouncing on Cynthion. """

from amaranth                       import Elaboratable, Module
from luna                           import top_level_cli
from luna.gateware.platform         import NullPin
from luna.gateware.interface.button import Debouncer


class ButtonDebouncer(Elaboratable):
    """ Gateware applet that debounces the user button on Cynthion
    and drives the debounced signal directly to all 6 user LEDs

    Parameters
    ----------
    debounce_ms: float
        The debounce duration, in milliseconds. Defaults to 20 ms.
    """

    def __init__(self, debounce_ms=20):
        self.debounce_ms = debounce_ms

    def elaborate(self, platform):
        m = Module()

        if platform is not None:
            button = platform.request_optional("button_user", default=NullPin())

            leds =   [platform.request_optional("led", i, default=NullPin())
                      for i in range(6)]
        else:
            button = NullPin()
            leds   = [NullPin() for _ in range(6)]

        m.submodules.debouncer = debouncer = Debouncer(button.i, debounce_ms=self.debounce_ms)

        # Have FPGA map debouncer.o signal to all 6 user LEDs.
        for led in leds:
            m.d.comb += led.o.eq(debouncer.o)

        return m


if __name__ == "__main__":
    top_level_cli(ButtonDebouncer)
