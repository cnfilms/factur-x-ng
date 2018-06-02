import io
import os
import yaml
import codecs
from io import BytesIO
from lxml import etree
from tempfile import NamedTemporaryFile
from datetime import datetime
import os.path
import mimetypes
import hashlib
from PyPDF2 import PdfFileReader
from PyPDF2.generic import IndirectObject
import json

from .flavors import xml_flavor
from .logger import logger
from .pdfwriter import FacturXPDFWriter

# Python 2 and 3 compat
try:
    file_types = (file, io.IOBase)
except NameError:
    file_types = (io.IOBase,)
unicode = str

__all__ = ['FacturX']


class FacturX(object):
    """Represents an electronic PDF invoice with embedded XML metadata following the
    Factur-X standard.

    The source of truth is always the underlying XML tree. No copy of field
    data is kept. Manipulation of the XML tree is either done via Python-style
    dict access (available for the most common fields) or by directly accessing
    the XML data on `FacturX.xml`.

    Attributes:
    - xml: xml tree of machine-readable representation.
    - pdf: underlying graphical PDF representation.
    - flavor: which flavor (Factur-x or Zugferd) to use.
    """

    def __init__(self, pdf_invoice, flavor='factur-x', level='minimum'):
        # Read PDF from path, pointer or string
        if isinstance(pdf_invoice, str) and pdf_invoice.endswith('.pdf') and os.path.isfile(pdf_invoice):
            with open(pdf_invoice, 'rb') as f:
                pdf_file = BytesIO(f.read())
        elif isinstance(pdf_invoice, str):
            pdf_file = BytesIO(pdf_invoice.encode('utf-8'))
        elif isinstance(pdf_invoice, file_types):
            pdf_file = pdf_invoice
        else:
            raise TypeError(
                "The first argument of the method get_facturx_xml_from_pdf must "
                "be either a string or a file (it is a %s)." % type(pdf_invoice))

        xml = self._xml_from_file(pdf_file)
        self.pdf = pdf_file

        # PDF has metadata embedded
        if xml is not None:
            self.xml = xml
            self.flavor = xml_flavor.XMLFlavor(xml)
            logger.info('Read existing XML from PDF. Flavor: %s', self.flavor.name)
        # No metadata embedded. Create from template.
        else:
            self.flavor, self.xml = xml_flavor.XMLFlavor.from_template(flavor, level)
            logger.info('PDF does not have XML embedded. Adding from template.')

        self.flavor.check_xsd(self.xml)
        self._namespaces = self.xml.nsmap

    def read_xml(self):
        """Use XML data from external file. Replaces existing XML or template."""
        pass

    def _xml_from_file(self, pdf_file):
        pdf = PdfFileReader(pdf_file)
        pdf_root = pdf.trailer['/Root']
        if '/Names' not in pdf_root or '/EmbeddedFiles' not in pdf_root['/Names']:
            logger.info('No existing XML file found.')
            return None

        for file in pdf_root['/Names']['/EmbeddedFiles']['/Names']:
            if isinstance(file, IndirectObject):
                obj = file.getObject()
                if obj['/F'] in xml_flavor.valid_xmp_filenames():
                    xml_root = etree.fromstring(obj['/EF']['/F'].getData())
                    xml_content = xml_root
                    xml_filename = obj['/F']
                    logger.info(
                        'A valid XML file %s has been found in the PDF file',
                        xml_filename)
                    return xml_content

    def __getitem__(self, field_name):
        path = self.flavor._get_xml_path(field_name)
        value = self.xml.xpath(path, namespaces=self._namespaces)
        if value is not None:
            value = value[0].text
        if 'date' in field_name:
            value = datetime.strptime(value, '%Y%m%d')
        return value

    def __setitem__(self, field_name, value):
        path = self.flavor._get_xml_path(field_name)
        res = self.xml.xpath(path, namespaces=self._namespaces)
        if len(res) > 1:
            raise LookupError('Multiple nodes found for this path. Refusing to edit.')

        if 'date' in field_name:
            assert isinstance(value, datetime), 'Please pass date values as DateTime() object.'
            value = value.strftime('%Y%m%d')
            res[0].attrib['format'] = '102'
            res[0].text = value
        else:
            res[0].text = value

    def is_valid(self):
        """Make every effort to validate the current XML.

        Checks:
        - all required fields are present and have values.
        - XML is valid
        - ...

        Returns: true/false (validation passed/failed)
        """
        pass

    def write_pdf(self, path):
        pdfwriter = FacturXPDFWriter(self)
        with open(path, 'wb') as output_f:
            pdfwriter.write(output_f)

        logger.info('XML file added to PDF invoice')
        return True

    @property
    def xml_str(self):
        """Calculate MD5 checksum of XML file. Used for PDF attachment."""
        return etree.tostring(self.xml, pretty_print=True)

    def write_xml(self, path):
        with open(path, 'wb') as f:
            f.write(self.xml_str)

    def __make_dict(self):
        field_file = os.path.join(os.path.dirname(__file__), 'flavors\\fields.yml')
        req_list = []
        with open(field_file, 'r') as f:
            data = f.read()
            dict_data = yaml.load(data)

        for k, v in dict_data.items():
            for kv, vv in v.items():
                if kv == '_required':
                    if vv is True:
                        req_list.append(k)

        factx_value = []
        factx_key = []
        zugf_key = []
        zugf_value = []

        for k, v in dict_data.items():
            for item in req_list:
                if k == item:
                    for vk, vv in v.items():
                        if vk == '_path':
                            for vvk, vvv in vv.items():
                                if vvk == 'factur-x':
                                    factx_key.append(k)
                                    factx_value.append(vvv)
                                elif vvk == 'zugferd':
                                    zugf_key.append(k)
                                    zugf_value.append(vvv)

        self.factx = {}

        for i in range(len(factx_key)):
            self.factx[factx_key[i]] = factx_value[i]

        self.zugf = {}

        for i in range(len(zugf_key)):
            self.zugf[zugf_key[i]] = zugf_value[i]

        self.zugf_ns = {'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:15',
              'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:12',
              'rsm': 'urn:ferd:CrossIndustryDocument:invoice:1p0',
              'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
              }

        self.factx_ns = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
              'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
              'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
              'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
              'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100'
              }

    def __export_file_from_xml(self, ns, xml_file_path, json_file_path, flavor):
        self.__make_dict()
        json_factx = {}

        # xml_file_path = os.path.join(os.path.dirname(__file__), 'text.xml')

        if flavor == 'factur-x':
            flavor_dict = self.factx
        elif flavor == 'zugferd':
            flavor_dict = self.zugf

        with open(xml_file_path, 'r') as xml_file:
            tree = etree.parse(xml_file)

            for k, v in flavor_dict.items():
                try:
                    r = tree.xpath(v, namespaces=ns)
                    json_factx[k] = r[0].text
                except IndexError:
                    json_factx[k] = None

        with open(json_file_path, 'w') as json_file:
            json.dump(json_factx, json_file, indent=4, sort_keys=True)

    def write_json_facturx(self, xml_file_path, json_file_path='factur_x.json'):
        ns = self.factx_ns

        self.__export_file_from_xml(ns, xml_file_path, json_file_path,  flavor='factur-x')

    def write_json_zugfred(self, xml_file_path, json_file_path='zugfred_x.json'):
        ns = self.zugf_ns

        self.__export_file_from_xml(ns, xml_file_path, json_file_path, flavor='zugferd')

    def __export_file_from_pdf(self, ns, tree, json_file_path, flavor):
        self.__make_dict()
        json_factx = {}

        # xml_file_path = os.path.join(os.path.dirname(__file__), 'text.xml')

        if flavor == 'factur-x':
            flavor_dict = self.factx
        elif flavor == 'zugferd':
            flavor_dict = self.zugf

        for k, v in flavor_dict.items():
            try:
                r = tree.xpath(v, namespaces=ns)
                json_factx[k] = r[0].text
            except IndexError:
                json_factx[k] = None

        with open(json_file_path, 'w') as json_file:
            json.dump(json_factx, json_file, indent=4, sort_keys=True)

    def write_json_facturx_from_pdf(self, pdf_path, json_file_path='facturx.json'):
        xml_data = self._xml_from_file(pdf_path)
        ns = self.factx_ns

        if xml_data is not None:
            self.__export_file_from_pdf(ns, xml_data, json_file_path, flavor='factur-x')
        else:
            logger.error("There is no embedded data in file")

    def write_json_zugfred_from_pdf(self, pdf_path, json_file_path='zugfred.json'):
        xml_data = self._xml_from_file(pdf_path)
        ns = self.zugf_ns

        if xml_data is not None:
            self.__export_file_from_pdf(ns, xml_data, json_file_path, flavor='zugferd')
        else:
            logger.error("There is no embedded data in file")