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

from .flavors import xml_flavor
from .logger import logger

try: # Python 2 and 3 compat
    file_types = (file, io.IOBase)
except NameError:
    file_types = (io.IOBase,)
unicode = str


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
            pdf_file = BytesIO(pdf_invoice)
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


    def _xml_from_file(self, pdf_file):
        pdf = PdfFileReader(pdf_file)
        pdf_root = pdf.trailer['/Root']
        if '/EmbeddedFiles' not in pdf_root['/Names']:
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

    def write_pdf(self, output_pdf_file):
        new_pdf_filestream = PdfFileWriter()
        new_pdf_filestream.appendPagesFromReader(original_pdf)

        xml_string = etree.tostring(self.xml, pretty_print=True)

        base_info = _extract_base_info(xml_root) # TODO: use my way to get metadata.
        pdf_metadata = _base_info2pdf_metadata(base_info)

        facturx_level = facturx_level.lower()
        if facturx_level not in FACTURX_LEVEL2xsd:
            if xml_root is None:
                xml_root = etree.fromstring(xml_string)
            logger.debug('Factur-X level will be autodetected')
            facturx_level = get_facturx_level(xml_root)

        _facturx_update_metadata_add_attachment(
            new_pdf_filestream, xml_string, pdf_metadata, facturx_level,
            output_intents=output_intents,
            additional_attachments=additional_attachments_read)


        if output_pdf_file:
            with open(output_pdf_file, 'wb') as output_f:
                new_pdf_filestream.write(output_f)
                output_f.close()
        else:
            if file_type == 'path':
                with open(pdf_invoice, 'wb') as f:
                    new_pdf_filestream.write(f)
                    f.close()
            elif file_type == 'file':
                new_pdf_filestream.write(pdf_invoice)
        logger.info('%s file added to PDF invoice', FACTURX_FILENAME)



        if output_pdf_file:
            with open(output_pdf_file, 'wb') as output_f:
                new_pdf_filestream.write(output_f)


    def write_xml(self, path):
        with open(path, 'wb') as f:
            xml_str = etree.tostring(self.xml, pretty_print=True)
            f.write(xml_str)


def _get_pdf_timestamp(date=None):
    if date is None:
        date = datetime.now()
    # example date format: "D:20141006161354+02'00'"
    pdf_date = date.strftime("D:%Y%m%d%H%M%S+00'00'")
    return pdf_date
