# ruff: noqa
from convoke.bases import Base
from convoke.signals import Signal


class BAR(Signal):
    pass


class Main(Base):
    dependencies = ["baz"]

    bars: list[BAR.Message] = Base.field(default_factory=list)

    @Base.responds(BAR)
    async def on_bar(self, obj):  # pragma: nocover
        self.bars.append(obj)
