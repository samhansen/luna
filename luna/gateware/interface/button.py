# amaranth: UnusedElaboratable=no
#
# This file is part of LUNA.
#
# Copyright (c) 2026 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2026 Sam Hansen <hansensc82@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

""" Button debouncing gateware. """

from amaranth         import Elaboratable, Module, Signal
from amaranth.lib.cdc import FFSynchronizer

__all__ = ["Debouncer"]


class Debouncer(Elaboratable):
    """ Gateware interface for debouncing button inputs.

    Attributes
    ----------
    i: Signal(), input
        Asynchronous raw button input signal.
    o: Signal(), output
        Debounced button level (high while pressed).
    pressed: Signal(), output
        Single-cycle strobe asserted on the rising edge of a debounced press.
    released: Signal(), output
        Single-cycle strobe asserted on the falling edge of a debounced release.

    Parameters
    ----------
    signal: Signal
        The raw button input signal to debounce.
    debounce_ms: float
        The debounce duration, in milliseconds. Defaults to 10 ms. This value
        may need to be tuned to the individual characteristics of the button or
        signal being debounced.
    warmup_ms: float | None
        Optional warmup period, in milliseconds. Defaults to None. warmup_ms is
        used to allow reset-transient signals to settle before debouncing
        begins. Set to 0 or None to disable warmup and begin debouncing
        immediately.
    """

    def __init__(self, signal, *, debounce_ms=10, warmup_ms=None):
        self.debounce_ms = debounce_ms
        self.warmup_ms = warmup_ms or 0

        #
        # I/O port
        #
        self.i        = signal
        self.o        = Signal()
        self.pressed  = Signal()
        self.released = Signal()

    def elaborate(self, platform):
        m = Module()

        if platform is not None:
            clk_f = int(getattr(platform, "default_clk_frequency", None) or 60e6)
        else:
            clk_f = int(1e6)

        debounce_cycles = max(1, int(clk_f * (self.debounce_ms / 1000)))
        warmup_cycles = max(1, int(clk_f * (self.warmup_ms / 1000)))

        max_cycles = max(debounce_cycles, warmup_cycles)

        counter   = Signal(range(max_cycles), name="counter")
        sync_i    = Signal(name="sync_i")
        debounced = Signal(name="debounced")
        running   = Signal(name="running")

        self.sync_i  = sync_i
        self.counter = counter

        m.submodules.sync_btn = FFSynchronizer(self.i, sync_i)
        m.d.comb += self.o.eq(debounced)

        # Default strobes to 0 every clock cycle.
        m.d.sync += [
            self.pressed.eq(0),
            self.released.eq(0),
        ]

        with m.FSM():
            with m.State("WARMUP"):
                if not self.warmup_ms:
                    m.next = "STABLE"
                else:
                    with m.If(counter == warmup_cycles):
                        m.next = "STABLE"
                    with m.Else():
                        m.d.sync += counter.eq(counter + 1)

            with m.State("STABLE"):
                m.d.sync += counter.eq(0)
                with m.If(sync_i != debounced):
                    m.next = "DEBOUNCING"

            with m.State("DEBOUNCING"):
                with m.If(sync_i == debounced):
                    m.d.sync += counter.eq(0)
                    m.next = "STABLE"
                with m.Elif(counter == debounce_cycles):
                    m.d.sync += [
                        debounced.eq(sync_i),
                        counter.eq(0),
                        self.pressed.eq(sync_i),
                        self.released.eq(~sync_i),
                    ]
                    m.next = "STABLE"
                with m.Else():
                    m.d.sync += counter.eq(counter + 1)

        return m
