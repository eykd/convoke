from setuptools import find_packages, setup

import versioneer

with open("README.rst", "r") as fi:
    long_description = fi.read()

setup(
    name="convoke",
    author="David Eyk",
    author_email="eykd@eykd.net",
    description="An app configuration toolkit that tries to do things right.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/eykd/convoke",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "configobj",
        "path",
        "pendulum",
    ],
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    python_requires='>=3.6',
)
