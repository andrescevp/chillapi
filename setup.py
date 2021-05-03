from setuptools import find_packages, setup

f = open("./chillapi/requirements.txt")
reqs = f.read().split('\n')

_test_reqs = [
        'psycopg2==2.8.6',
        'Faker==8.1.0',
        'alembic==1.5.8'
        ]

setup(
        name = 'chillapi',
        packages = find_packages(include = ['chillapi.*']),
        version = '0.1.0',
        description = 'A library to create APIs focused on data projects',
        author = 'andrescevp@gmail.com',
        license = 'MIT',
        install_requires = reqs,
        extras_require = {
                'testing': _test_reqs
                },
        # setup_requires = ['unittest'],
        tests_require = _test_reqs,
        test_suite = 'setup_tests',
        python_requires = '>=3.8',
        keywords = ['python', 'api', 'codeless', 'data']
        )
