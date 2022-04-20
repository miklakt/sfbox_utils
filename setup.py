import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

setup(
    name='sfbox_utils',
    version='0.0.2',
    description='Pandas DataFrame interface for sfbox (namics)',
    author='Laktionov Mikhail',
    author_email = 'miklakt@gmail.com',
    packages=['sfbox_utils'],
    install_requires=['numpy','pandas'],
    scripts=['sfbox_utils/scripts/call_sfbox_multifile.sh', 'sfbox_utils/scripts/split_output.sh'],
    include_package_data=True,
)