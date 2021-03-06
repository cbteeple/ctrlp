from setuptools import setup, find_packages

setup(
    name='ctrlp',
    version='1.0.5',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    license='MIT',
    description='Low-level hardware interface for Ctrl-P pressure control systems.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'seaborn',
        'PyYAML',
        'pyserial',
    ],
    url='https://github.com/cbteeple/ctrlp',
    author='Clark Teeple',
    author_email='cbteeple@gmail.com',
    classifiers=[
        # How mature is this project? Common values are
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: System :: Hardware :: Hardware Drivers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',

        # Specify the Python versions you support here.
        'Programming Language :: Python :: 3',
    ]
)