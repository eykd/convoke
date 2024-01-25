# ruff: noqa
from convoke.bases import Base
from convoke.configs import BaseConfig, env_field
from convoke.signals import Signal


class FOO(Signal):
    pass


class FooConfig(BaseConfig):
    BAR: str = env_field(default="baz")


class Main(Base):
    config_class = FooConfig

    foos: list[FOO.Message] = Base.field(init=False)

    # Circular dependency!
    dependencies = ["baz"]

    def on_init(self):
        self.foos = []

    @Base.responds(FOO)
    def on_foo(self, obj: FOO.Message):  # pragma: nocover
        self.foos.append(obj)
