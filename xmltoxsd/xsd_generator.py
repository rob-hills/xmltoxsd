from lxml import etree
from .xml_parser import load_xml
from .schema_inferer import infer_type

class XSDGenerator:
    XSD_FAILURE_ERROR_MESSAGE = 'Failed to generate XSD schema.'

    @property
    def xsd(self) -> etree.Element: return self._xsd

    @xsd.setter
    def xsd(self, value:etree.Element):
        self._xsd = value

    def __init__(self, xml_path:str, min_occurs="0"):
        self.ns_map = {"xs": "http://www.w3.org/2001/XMLSchema"}
        self._xsd = None
        self._xsd_as_string = None
        self._xsd_as_pretty_string = None
        self.__generate_xsd(xml_path, min_occurs)

    def __generate_xsd(self, xml_path:str, min_occurs="0"):
        """
        Generates an XSD schema (etree.Element) for the given XML file.

        Parameters:
        - xml_path (str): Path to the XML file.
        - min_occurs (str): Default minOccurs value for elements.
        """
        self._xsd_as_string = None
        self._xsd_as_pretty_string = None
        xml_tree = load_xml(xml_path)
        if xml_tree is not None:
            self._xsd = etree.Element("{http://www.w3.org/2001/XMLSchema}schema", nsmap=self.ns_map)
            self.process_element(xml_tree.getroot(), self._xsd, min_occurs=min_occurs, is_first_element=True)
        else:
            self._xsd_as_string = self.XSD_FAILURE_ERROR_MESSAGE
            self._xsd_as_pretty_string = self.XSD_FAILURE_ERROR_MESSAGE

    @property
    def xsd_as_string(self) -> str:
        if self._xsd_as_string is None:
            if self.xsd is None:
                self._xsd_as_string = self.XSD_FAILURE_ERROR_MESSAGE
            else:
                self._xsd_as_string = etree.tostring(self.xsd, pretty_print=False).decode()
        return self._xsd_as_string


    @property
    def xsd_as_pretty_string(self) -> str:
        if self._xsd_as_pretty_string is None:
            if self.xsd is None:
                self._xsd_as_pretty_string = self.XSD_FAILURE_ERROR_MESSAGE
            else:
                self._xsd_as_pretty_string = etree.tostring(self.xsd, pretty_print=True).decode()
        return self._xsd_as_pretty_string


    def process_element(self, element, parent, min_occurs="1", is_first_element=False):
        """
        Recursively processes an XML element to generate its XSD representation.

        Parameters:
        - element (etree.Element): The current XML element.
        - parent (etree.Element): The parent element in the XSD schema.
        - min_occurs (str): The minOccurs value for the element.
        - is_first_element (bool): Flag to indicate the first element being processed
        """
        ns = "{http://www.w3.org/2001/XMLSchema}"
        element_name = element.tag.split('}')[-1]
        same_element = parent.find(f"./*[@name='{element_name}']")
        if same_element is None:
            if is_first_element:
                element_def = etree.SubElement(parent, f"{ns}element", name=element_name)
            else:
                element_def = etree.SubElement(parent, f"{ns}element", name=element_name, minOccurs=min_occurs, maxOccurs="1")

            if len(element) > 0 or len(element.attrib):
                complex_type = etree.SubElement(element_def, f"{ns}complexType")
                sequence = etree.SubElement(complex_type, f"{ns}sequence")
                for child in element:
                    self.process_element(child, sequence, min_occurs)
                for attr_name, attr_value in element.attrib.items():
                    attr_type = infer_type(attr_value)
                    etree.SubElement(complex_type, f"{ns}attribute", name=attr_name, type=attr_type)
            else:
                element_def.set('type', infer_type(element.text))

if __name__ == "__main__":
    xml_path = "tests/xml_files/valid_basic.xml"  # Update this path to your XML file.
    generator = XSDGenerator(xml_path, min_occurs="0")
    print(generator.xsd_as_pretty_string)
