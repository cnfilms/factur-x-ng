import os
import unittest
from facturx.facturx import *


class TestReading(unittest.TestCase):
    def setUp(self):
        self.test_files_dir = os.path.join(os.path.dirname(__file__), 'sample_invoices')
        self.test_files = os.listdir(self.test_files_dir)

    def test_from_file(self):
        for file in self.test_files:
            file_path = os.path.join(self.test_files_dir, file)
            FacturX(file_path)

    # returning file path for a specific file in 'sample_invoices'
    def find_file(self, file_name):
        for file in self.test_files:
            if file == file_name:
                file_path = os.path.join(self.test_files_dir, file)
                return file_path

    # def test_input_error(self):
    #     with self.assertRaises(TypeError) as context:
    #         FacturX('non-existant.pdf')

    def test_file_without_embedded_data(self):
        file_path = self.find_file('no_embedded_data.pdf')
        self.assertEqual(FacturX(file_path)._xml_from_file(file_path), None)

    def test_file_embedded_data(self, file_name='embedded_data.pdf'):
        file_path = self.find_file(file_name)
        if FacturX(file_path)._xml_from_file(file_path) is None:
            self.assertTrue(False, "The PDF file has no embedded file")
        else:
            self.assertTrue(True)

    def test_write_pdf(self):
        file_path = self.find_file('no_embedded_data.pdf')
        factx = FacturX(file_path)
        test_file_path = os.path.join(self.test_files_dir, 'test.pdf')

        # checking if pdf file is made
        factx.write_pdf(test_file_path)
        self.assertTrue(os.path.isfile(test_file_path))
        self.setUp()

        # checking that xml is embedded
        if self.test_file_embedded_data(file_name='test.pdf') is None:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
        os.remove(test_file_path)


    def test_write_xml(self):
        pass


def main():
    unittest.main()


if __name__ == '__main__':
    main()
