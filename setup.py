from setuptools import setup

setup(name='fftraffic-scanner',
      version='0.1.0',
      description='Python tool for scanning PokerStars traffic',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3.6',
          'Topic :: Utilities',
      ],
      url='https://bitbucket.org/vyvojer/fftraffic-scanner',
      author='Alexey Londkevich',
      author_email='vyvojer@gmail.com',
      packages=['scanner'],
      package_data={
          'scanner': ['pokerstars_characters.dat', 'pokerstars_flags.dat']
      },
      requires=['requests', 'pywinauto', 'win32gui', 'Pillow'],
      zip_safe=False)