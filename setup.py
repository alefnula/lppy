import io
import importlib.util
from pathlib import Path
from setuptools import setup, find_packages

author = "Viktor Kerkez"
author_email = "alefnula@gmail.com"


def get_version():
    """Import the version module and get the project version from it."""
    version_py = Path(__file__).parent / "lppy" / "version.py"
    spec = importlib.util.spec_from_file_location("version", version_py)
    version = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version)
    return version.__version__


setup(
    name="lppy",
    version=get_version(),
    author=author,
    author_email=author_email,
    maintainer=author,
    maintainer_email=author_email,
    description="Python library for controlling Novation Launchpads.",
    long_description=io.open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/alefnula/lppy",
    platforms=["Windows", "POSIX", "MacOSX"],
    license="Apache-2.0",
    packages=find_packages(),
    install_requires=io.open("requirements.txt").read().splitlines(),
    entry_points="""
        [console_scripts]
        lppy=lppy.__main__:cli
    """,
)
