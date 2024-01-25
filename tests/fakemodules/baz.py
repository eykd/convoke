# ruff: noqa
from typing import Callable

from convoke.bases import Base
from convoke.mountpoints import Mountpoint
from convoke.signals import Signal


class BAZ(Signal):
    pass


class ThingyMadoodle(Mountpoint):
    pass


class Main(Base):
    # Circular dependency!
    dependencies = ["foo"]

    things: list[str] = Base.field(default_factory=list)
    other_things: list[str] = Base.field(default_factory=list)

    @Base.responds(BAZ)
    def on_baz(self, obj: BAZ.Message):
        for thinger in self.thingers:
            thinger(obj.value)

    @property
    def thingers(self) -> list[Callable[[str], None]]:
        return list(self.hq.mountpoints[ThingyMadoodle].mounted)

    @ThingyMadoodle.register
    def do_a_thing(self, value):
        self.things.append(value)

    @ThingyMadoodle.register
    def do_another_thing(self, value):
        self.other_things.append(value)
