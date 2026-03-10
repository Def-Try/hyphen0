from setuptools import setup, find_packages

setup(
    name='hyphen0',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'asyncio',
        'pycryptodome',
        'ua-generator'
    ],
    author='googer_',
    author_email='googer760@gmail.com',
    description='DPI and human inspection resistant data transfer protocol',
    url='github.com/Def-Try/hyphen0',
)