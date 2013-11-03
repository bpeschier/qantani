from setuptools import setup

with open('README.md') as file:
    long_description = file.read()

setup(
    name='Qantani',
    version='0.1.dev1',
    packages=['qantani',],
    license='MIT',
    long_description=long_description,
    classifiers=[
        'Programming Language :: Python :: 3.3',
    ],
)