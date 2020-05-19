Convoke
=======

An app configuration toolkit that tries to do things right.

Install
-------

Convoke is available from PyPI::

    pip install convoke

Usage
-----

Create a Settings object::

    from convoke import Settings

    settings = Settings('My App Name')

Convoke will pull settings from three places, in order of priority:

1. Local overrides::

    Settings('My App Name', foo='bar')

2. ``os.environ`` values (upper-cased)::

    settings.get('foo') == os.environ.get('FOO')

3. a provided INI-style configuration filepath *or* ``config.ini`` in the
   OS-specific application directory::

    # ~/.config/config.ini (or OS equivalent)
    foo = bar
      
The ``Settings`` object provides convenience accessors for different value types:

- **Strings**::

    settings['foo']
    settings.get('foo', default='blah')

- **Boolean**::

    settings.as_bool('foo', default='True')

- **Integer**::

    settings.as_int('foo', default='5')

- **Float**::

    settings.as_float('foo', default='5.0')

- **Path** (returns ``path.Path`` objects)::

    settings.as_path('foo', default='~/blah')

For simple usage, there's also a singleton ``Settings`` mode::

    settings = convoke.get_settings('My App Name', foo='bar')
    assert settings.app_name == 'My App Name'
    assert settings['foo'] == 'bar'

    # Further calls to get_settings returns the same object:
    settings2 = convoke.get_settings()
    assert settings2 is settings

    # Future overrides have no effect:
    settings2 = convoke.get_settings('Some other name', foo='blah')
    assert settings.app_name == 'My App Name'
    assert settings['foo'] == 'bar'
