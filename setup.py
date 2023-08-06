"""setup.py"""
from os import path
from setuptools import setup, find_packages
from dotdrop.version import __version__ as VERSION


README = 'README.md'
here = path.abspath(path.dirname(__file__))


def read_readme(readme_path):
    """read readme content"""
    with open(readme_path, encoding="utf-8") as file:
        return file.read()


REQUIRES_PYTHON = '>=3'
URL = f'https://github.com/deadc0de6/dotdrop/archive/v{VERSION}.tar.gz'

setup(
    name='dotdrop',
    version=VERSION,

    description='Save your dotfiles once, deploy them everywhere',
    long_description=read_readme(README),
    long_description_content_type="text/markdown; variant=GFM",
    url='https://github.com/deadc0de6/dotdrop',
    download_url=URL,
    options={"bdist_wheel": {"python_tag": "py3"}},
    # include anything from MANIFEST.in
    include_package_data=True,

    author='deadc0de6',
    author_email='deadc0de6@foo.bar',

    license='GPLv3',
    python_requires=REQUIRES_PYTHON,
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          ],

    keywords='dotfiles jinja2',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'docopt', 'Jinja2', 'ruamel.yaml',
        'python-magic', 'packaging', 'requests',
        'tomli; python_version < "3.11"',
        'tomli_w', 'distro'],

    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },

    entry_points={
        'console_scripts': [
            'dotdrop=dotdrop:main',
        ],
    },
)
