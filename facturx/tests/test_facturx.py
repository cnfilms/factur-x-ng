import os
import unittest
from facturx.facturx import *
import xml.etree.ElementTree as ET


class XmlTree:
    def __init__(self):
        pass

    @staticmethod
    def convert_string_to_tree( xmlString):

        return ET.fromstring(xmlString)

    def xml_compare(self, x1, x2):
        if x1.tag != x2.tag:
            # print('Tags do not match: %s and %s' % (x1.tag, x2.tag))
            return False
        for name, value in x1.attrib.items():
            if x2.attrib.get(name) != value:
                # print('Attributes do not match: %s=%r, %s=%r'
                #              % (name, value, name, x2.attrib.get(name)))
                return False
        for name in x2.attrib.keys():
            if name not in x1.attrib:
                # print('x2 has an attribute x1 is missing: %s'
                #              % name)
                return False
        if not self.text_compare(x1.text, x2.text):
            # print('text: %r != %r' % (x1.text, x2.text))
            return False
        if not self.text_compare(x1.tail, x2.tail):
            # print('tail: %r != %r' % (x1.tail, x2.tail))
            return False
        cl1 = x1.getchildren()
        cl2 = x2.getchildren()
        if len(cl1) != len(cl2):
            # print('children length differs, %i != %i'
            #              % (len(cl1), len(cl2)))
            return False
        i = 0
        for c1, c2 in zip(cl1, cl2):
            i += 1
            if not self.xml_compare(c1, c2):
                # print('children %i do not match: %s'
                #              % (i, c1.tag))
                return False
        return True

    def text_compare(self, t1, t2):
        if not t1 and not t2:
            return True
        if t1 == '*' or t2 == '*':
            return True
        return (t1 or '').strip() == (t2 or '').strip()


class TestReading(unittest.TestCase):
    def discover_files(self):
        self.test_files_dir = os.path.join(os.path.dirname(__file__), 'sample_invoices')
        self.test_files = os.listdir(self.test_files_dir)

    def test_from_file(self):
        self.discover_files()
        for file in self.test_files:
            file_path = os.path.join(self.test_files_dir, file)
            FacturX(file_path)

    # returning file path for a specific file in 'sample_invoices'
    def find_file(self, file_name):
        self.discover_files()
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
        self.discover_files()

        # checking that xml is embedded
        if self.test_file_embedded_data(file_name='test.pdf') is None:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
        os.remove(test_file_path)


    def test_write_xml(self):
        compare_file_dir = os.path.join(os.path.dirname(__file__), 'compare')
        expected_file_path = os.path.join(compare_file_dir, 'no_embedded_data.xml')
        test_file_path = os.path.join(compare_file_dir, 'test.xml')

        factx = FacturX(self.find_file('no_embedded_data.pdf'))
        factx.write_xml(test_file_path)
        self.assertTrue(os.path.isfile(test_file_path))

        with open(expected_file_path, 'r') as expected_file, open(test_file_path, 'r') as test_file:
            expected_file_tree = XmlTree.convert_string_to_tree(expected_file.read())
            test_file_tree = XmlTree.convert_string_to_tree(test_file.read())

            comparator = XmlTree()

            if comparator.xml_compare(expected_file_tree, test_file_tree):
                self.assertTrue(True)
            else:
                self.assertTrue(False, "Files don't match")

        os.remove(test_file_path)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
