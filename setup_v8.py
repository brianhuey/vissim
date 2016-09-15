# -*- coding: utf-8 -*-
"""

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join('../README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vissim_v8',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='1.0.0',

    description='Parse and manipulate VISSIM v8.x models',
    long_description=long_description,

    # The project's main homepage.
    url='http://github.com/brianhuey/vissim',

    # Author details
    author='S. Brian Huey',
    author_email='sbhuey@gmail.com',

    # Choose your license
    license='BSD License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Pre-Alpha',
        
        # Indicate the environment the project is to be used in
        'Environment :: Console',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    # What does your project relate to?
    keywords='vissim traffic transportation modeling',
    
    # Is your project is safe to be zipped?
    zip_safe=True,

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # packages=find_packages(exclude=[]),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
       py_modules=["vissim_objs", "__init__", "osm_to_graph", "osm_to_vissim"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
#    extras_require={
#        'dev': ['check-manifest'],
#        'test': ['coverage'],
#    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
#    package_data={
#        'sample': ['package_data.dat'],
#    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
#    data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
#    entry_points={
#        'console_scripts': [
#            'sample=sample:main',
#        ],
#    },
)