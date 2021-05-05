from os import path

from setuptools import find_packages, setup

f = open("./chillapi/requirements.txt")
reqs = f.read().split('\n')

_test_reqs = [
        'psycopg2==2.8.6',
        'Faker==8.1.0',
        'alembic==1.5.8'
        ]

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding = 'utf-8') as f:
    long_description = f.read()

setup(
        name = 'chillapi',
        packages = find_packages(include = ['chillapi', 'chillapi.*']),
        version = '0.0.1',
        description = 'A library to create APIs focused on data projects',
        long_description = long_description,
        long_description_content_type = 'text/markdown',
        author = 'andrescevp@gmail.com',
        license = 'MIT',
        install_requires = reqs,
        extras_require = {
                'testing': _test_reqs
                },
        tests_require = _test_reqs,
        test_suite = 'setup_tests',
        python_requires = '>=3.8',
        keywords = ['python', 'api', 'codeless', 'data'],
        include_package_data = True,
        )
