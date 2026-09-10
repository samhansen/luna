# amaranth: UnusedElaboratable=no
#
# This file is part of LUNA.
#
# Copyright (c) 2026 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2026 Sam Hansen <hansensc82@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from luna.gateware.test         import LunaGatewareTestCase, sync_test_case
from amaranth                   import Signal
from luna.gateware.interface.button import Debouncer


class ButtonTest(LunaGatewareTestCase):
    """ Test case for Button debouncing and edge detection. """

    DEBOUNCE_CYCLES = 10

    def instantiate_dut(self):
        self.btn_in = Signal(name="btn_raw")
        # platform is None, so default frequency is 1MHz; 0.01ms = 10 cycles.
        return Debouncer(self.btn_in, debounce_ms=0.01)

    def traces_of_interest(self):
        return (
            self.btn_in,
            self.dut.o,
            self.dut.pressed,
            self.dut.released,
        )

    def initialize_signals(self):
        yield self.btn_in.eq(0)

    @sync_test_case
    def test_debouncing_and_edge_pulses(self):
        dut = self.dut

        # Initial state should be unpressed
        yield from self.advance_cycles(5)
        self.assertEqual((yield dut.o), 0)
        self.assertEqual((yield dut.pressed), 0)
        self.assertEqual((yield dut.released), 0)

        # Contact bounce on press (short pulses should be rejected)
        yield self.btn_in.eq(1)
        yield from self.advance_cycles(2)
        yield self.btn_in.eq(0)
        yield from self.advance_cycles(2)
        yield self.btn_in.eq(1)
        yield from self.advance_cycles(3)
        yield self.btn_in.eq(0)
        yield from self.advance_cycles(1)

        # Button should still be unpressed because bounces were shorter than debounce time
        self.assertEqual((yield dut.o), 0)
        self.assertEqual((yield dut.pressed), 0)

        # Stable button press
        yield self.btn_in.eq(1)
        pressed_seen = False
        for _ in range(self.DEBOUNCE_CYCLES + 10):
            yield
            if (yield dut.pressed):
                pressed_seen = True
                self.assertEqual((yield dut.o), 1)
                break

        self.assertTrue(pressed_seen)
        # Verify strobe deasserts after exactly 1 cycle
        yield
        self.assertEqual((yield dut.pressed), 0)
        self.assertEqual((yield dut.o), 1)

        # Glitch while held should be filtered out
        yield self.btn_in.eq(0)
        yield from self.advance_cycles(2)
        yield self.btn_in.eq(1)
        yield from self.advance_cycles(5)
        self.assertEqual((yield dut.o), 1)
        self.assertEqual((yield dut.released), 0)

        # Contact bounce on release
        yield self.btn_in.eq(0)
        yield from self.advance_cycles(2)
        yield self.btn_in.eq(1)
        yield from self.advance_cycles(2)
        yield self.btn_in.eq(0)

        # Stable release
        released_seen = False
        for _ in range(self.DEBOUNCE_CYCLES + 10):
            yield
            if (yield dut.released):
                released_seen = True
                self.assertEqual((yield dut.o), 0)
                break

        self.assertTrue(released_seen)
        # Verify strobe deasserts after exactly 1 cycle
        yield
        self.assertEqual((yield dut.released), 0)
        self.assertEqual((yield dut.o), 0)
