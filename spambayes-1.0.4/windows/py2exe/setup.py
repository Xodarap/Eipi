from distutils.core import setup
import py2exe

py2exe_options = dict(
    packages = "",
    excludes = "",
    includes = "weakref",
)

tester = dict(
    script = "temp.py",
    dest_base = "test",
)

setup(name="Tester",
      windows=[tester],
      options = {"py2exe" : py2exe_options},
)
