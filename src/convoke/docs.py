"""Tools for working with docstrings"""
import textwrap

import funcy as fn


def format_object_docstring(obj, wrap: int = 0):
    """Format an object's docstring to normalize indentation.

    Optionally, wrap lines to a maximum length.
    """
    return format_docstring(getattr(obj, "__doc__", None) or "", wrap=wrap)


def format_docstring(doc: str, wrap: int = 0):
    """Format a string as a docstring."""
    lines = doc.strip().splitlines()
    if lines:
        head = fn.first(lines)
        rest = textwrap.dedent("\n".join(fn.rest(lines))).strip()
        if wrap:
            wrapper = textwrap.TextWrapper(width=wrap, break_long_words=False, break_on_hyphens=False)
            rest = "\n\n".join(wrapper.fill(line) for line in rest.split("\n\n"))
        doc = f"{head}\n\n{rest}".rstrip()
    return doc


def comment_lines(text: str, comment="#"):
    """Format lines with prepended line comments."""
    return "\n".join(f"{comment} {line}".rstrip() for line in text.splitlines())
