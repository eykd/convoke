# ruff: noqa: D100, D101, D102, D103
import textwrap

from convoke import docs


class TestFormatDocstring:
    def test_it_should_format_a_missing_docstring(self):
        class Foo:
            pass

        result = docs.format_object_docstring(Foo)
        expected = ""
        assert result == expected

    def test_it_should_format_a_single_line_docstring(self):
        class Foo:
            """Foo docs"""

        result = docs.format_object_docstring(Foo)
        expected = "Foo docs"
        assert result == expected

    def test_it_should_format_a_multiline_docstring(self):
        class Foo:
            """Foo docs

            Some more detail.
            """

        result = docs.format_object_docstring(Foo)
        expected = "Foo docs\n\nSome more detail."
        assert result == expected

    def test_it_should_format_and_fill_a_multiline_docstring(self):
        class Foo:
            """Foo docs

            West city organization sell learn different professional. Environment by it possible. Main win doctor
            book arrive shoulder.

            View personal me type marriage beautiful. While prove throughout idea memory. Condition company effect
            idea PM.

            To woman especially hour wonder trade all west.

            Bed success part. Image great owner tonight treatment agent quickly.

            Both be any institution force. At tend military understand billion process challenge our. Nice office
            author bar type.

            http://example.com/this-is-a-really-long-url-that-should-not-be-wrapped-onto-multiple-lines-i-mean-it-ok-thank-you
            """

        result = docs.format_object_docstring(Foo, wrap=40)
        expected = textwrap.dedent(
            """
            Foo docs

            West city organization sell learn
            different professional. Environment by
            it possible. Main win doctor book arrive
            shoulder.

            View personal me type marriage
            beautiful. While prove throughout idea
            memory. Condition company effect idea
            PM.

            To woman especially hour wonder trade
            all west.

            Bed success part. Image great owner
            tonight treatment agent quickly.

            Both be any institution force. At tend
            military understand billion process
            challenge our. Nice office author bar
            type.

            http://example.com/this-is-a-really-long-url-that-should-not-be-wrapped-onto-multiple-lines-i-mean-it-ok-thank-you
            """
        ).strip()
        assert result == expected


class TestCommentLines:
    def test_it_should_comment_a_multiline_docstring(self):
        docstring = "Foo docs\n\nSome more detail."

        result = docs.comment_lines(docstring)
        expected = "# Foo docs\n#\n# Some more detail."
        assert result == expected
