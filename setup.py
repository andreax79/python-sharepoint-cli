#!/usr/bin/env python
import os
import os.path
from setuptools import setup, find_packages
from sharepointcli import __version__

this_directory = os.path.abspath(os.path.dirname(__file__))
install_requires = [line.rstrip() for line in open(os.path.join(this_directory, 'requirements.txt'))]
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='sharepointcli',
      version=__version__,
      description='Command line interface for SharePoint',
      long_description=long_description,
      long_description_content_type='text/markdown',
      classifiers=[
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
      ],
      keywords='sharepoint cli',
      author='Andrea Bonomi',
      author_email='andrea.bonomi@gmail.com',
      url='http://github.com/andreax79/python-sharepoint-cli',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples']),
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires,
      entry_points={
          'console_scripts': [
              'spo=sharepointcli.cli:main',
          ],
      },
      test_suite='test',
      tests_require=['nose'])
