try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    from values import internal_config
except ImportError:
    from values import internal_config

setup(
    name=internal_config.PROGRAM_NAME,
    version=internal_config.VERSION,
    license=internal_config.LICENSE,
    description=internal_config.DESCRIPTION,
    long_description="",
    author=internal_config.AUTHOR,
    author_email=internal_config.AUTHOR_EMAIL,
    keywords="battery monitor linux light configurable",
    scripts=['battmon']
)
