from setuptools import setup, find_packages
import os
import re

from text_adventure_games import __version__

base_game_install_reqs = ['jupyter', 'graphviz']

with open("README.md", "r") as fh:
    long_description = fh.read()

with open(os.path.join(__file__, "requirements.txt"), 'r') as reqs:
    install_packages = [req for req in reqs.read().split('\n') if not re.match(r"#\s?", req) and req]
    install_packages.extend(base_game_install_reqs)

setup(
    name='text adventure games',
    version=__version__,
    author='Generative Agents Framework: Samuel Thudium, Federico Cimini; Base game Framework: Chris Callison-Burch, Jms Dnns',
    author_email='sam.thudium1@gmail.com; ccb@upenn.edu',
    # description='A framework for building text based RPGs',
    description='A framework for building episodic and competitive text-based RPGs with generative agents.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://interactive-fiction-class.org/',
    # license='',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_packages,
    extras_require={
        'dev': [
            'black',
            'nbformat'
        ],
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ]
)
