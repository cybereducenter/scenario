import sys
from setuptools import setup

'''
if sys.version_info[0] != 2:
    sys.stderr.write('This package only supports Python 2.\n')
    sys.exit(1)
'''
setup(name='scenario',
      version='2.1.0',
      packages=['scenario',
                'scenario.api',
                'scenario.player',
                'scenario.parser',
                'scenario.unittest',
                'scenario.reporter',
                'scenario.tests'],
      package_dir={'scenario': 'scenario'},
      package_data={'scenario': ['formats/html/index.html',
                                 'formats/html/*/*',
                                 'schema/*'],
                                 'scenario.reporter': ['templates/*.j2',],},
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
      ],
      install_requires=['pexpect', 'jsonschema', 'nose', "Jinja2>=3.0.0"],
      entry_points={
          'console_scripts': [
              'scenario = scenario.__main__:main'
          ]
      },
      test_suite='nose.collector',
      tests_require=['nose'],
      )
