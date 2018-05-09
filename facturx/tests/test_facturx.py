import os
import unittest
from facturx.facturx import FacturX

# Here's our "unit".
def IsOdd(n):
    return n % 2 == 1

# Here's our "unit tests".
class IsOddTests(unittest.TestCase):

    def testOne(self):
        self.failUnless(IsOdd(1))

    def testTwo(self):
        self.failIf(IsOdd(2))

class TestReading(unittest.TestCase):

    def setUp(self):
        self.test_files_dir = os.path.join(os.path.dirname(__file__), 'sample_invoices')
        self.test_files = os.listdir(self.test_files_dir)

    def testFromFile(self):
        for file in self.test_files:
            file_path = os.path.join(self.test_files_dir, file)
            FacturX(file_path)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
