import os
import unittest
from facturx.facturx import FacturX

class TestReading(unittest.TestCase):
    def setUp(self):
        self.test_files_dir = os.path.join(os.path.dirname(__file__), 'sample_invoices')
        self.test_files = os.listdir(self.test_files_dir)

    def test_from_file(self):
        for file in self.test_files:
            file_path = os.path.join(self.test_files_dir, file)
            FacturX(file_path)

    def test_input_error(self):
        with self.assertRaises(TypeError) as context:
            FacturX('non-existant.pdf')

def main():
    unittest.main()

if __name__ == '__main__':
    main()
