from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

version = "0.0.1"

setup(name='vhostino',
      version=version,
      description="Virtual Hosts Plugin for Mozilla Circus",
      long_description=README,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Alessandro Molina',
      author_email='amol@turbogears.org',
      url='https://github.com/amol-/vhostino',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'gevent',
          'circus'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
