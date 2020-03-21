from cached_property import cached_property
from lxml import etree

from xsd2go.xsd.util import parse_ref_value
from .base import Node


class Element(Node):
    def __init__(self, schema, node):
        super(Element, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.add_element(self)

    @cached_property
    def name(self):
        _name = self.node.attrib.get('name')

        if _name is None and self.ref_element is not None:
            _name = self.ref_element.name

        if _name is None:
            raise RuntimeError(
                "Cannot get name from %s" % self.tostring())
        return _name

    @cached_property
    def ref_element(self):
        ref_name = self.node.attrib.get('ref')
        if ref_name is not None:
            ref_element = self.schema.get_element(ref_name)
            if ref_element is None:
                raise RuntimeError(
                    "Cannot find ref element for %s" % self.tostring())
            return ref_element
        return None

    @cached_property
    def type_instance(self):
        if self.nested_type is not None:
            return self.nested_type
        elif self.ref_element is not None:
            return self.ref_element.type_instance
        else:
            type_name, type_ns = parse_ref_value(
                self.node.attrib['type'], self.schema.nsmap)
            refered_type_instance = self.schema.get_type_instance(
                type_name, type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance

    @property
    def max_occrs(self):
        return self.node.attrib.get("maxOccurs", "1")

    @property
    def min_occrs(self):
        return self.node.attrib.get("minOccurs", "1")

    @property
    def is_list(self):
        return self.max_occrs != "1"

    def _parse(self):
        from .simple_type import SimpleType
        from .complex_type import ComplexType
        self.nested_type = None

        simple_type_node = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_node:
            self.nested_type = SimpleType(self.schema, simple_type_node[0])

        complex_type_node = self.node.xpath(
            "xsd:complexType",
            namespaces=self.schema.nsmap
        )

        if complex_type_node:
            self.nested_type = ComplexType(self.schema, complex_type_node[0])
