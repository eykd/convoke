# ruff: noqa: D100, D103
# Lifted from https://github.com/encode/starlette/blob/2ca746642d7c5b64dbab430e590a89170eb14614/tests/test__utils.py
#
# Copyright © 2018, [Encode OSS Ltd](https://www.encode.io/).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import functools

from convoke.inspectors import is_async_callable


def test_async_func():
    async def async_func():
        ...  # pragma: no cover

    def func():
        ...  # pragma: no cover

    assert is_async_callable(async_func)
    assert not is_async_callable(func)


def test_async_partial():
    async def async_func(a, b):
        ...  # pragma: no cover

    def func(a, b):
        ...  # pragma: no cover

    partial = functools.partial(async_func, 1)
    assert is_async_callable(partial)

    partial = functools.partial(func, 1)
    assert not is_async_callable(partial)


def test_async_method():
    class Async:
        async def method(self):
            ...  # pragma: no cover

    class Sync:
        def method(self):
            ...  # pragma: no cover

    assert is_async_callable(Async().method)
    assert not is_async_callable(Sync().method)


def test_async_object_call():
    class Async:
        async def __call__(self):
            ...  # pragma: no cover

    class Sync:
        def __call__(self):
            ...  # pragma: no cover

    assert is_async_callable(Async())
    assert not is_async_callable(Sync())


def test_async_partial_object_call():
    class Async:
        async def __call__(self, a, b):
            ...  # pragma: no cover

    class Sync:
        def __call__(self, a, b):
            ...  # pragma: no cover

    partial = functools.partial(Async(), 1)
    assert is_async_callable(partial)

    partial = functools.partial(Sync(), 1)
    assert not is_async_callable(partial)


def test_async_nested_partial():
    async def async_func(a, b):
        ...  # pragma: no cover

    partial = functools.partial(async_func, b=2)
    nested_partial = functools.partial(partial, a=1)
    assert is_async_callable(nested_partial)
