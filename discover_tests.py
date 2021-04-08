import os
import unittest
import argparse

os.environ.setdefault('__CHILLAPI_SETUP_TESTING__', 'false')
parser = argparse.ArgumentParser(description='Suite discovery')
parser.add_argument('suite', default = 'settime')

args = parser.parse_args()

loader = unittest.TestLoader()
tests = loader.discover(f'./tests/{args.suite}')
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
