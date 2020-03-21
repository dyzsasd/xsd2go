from cached_property import cached_property

from xsd2go.xsd.util import parse_ref_value, parse_tag
from xsd2go.constants import XSD_NS

from .base import Node
from .base_type import name2base_class
from .type_decorator import SimpleTypeRestriction, List, Union


class SimpleType(Node):
    def __init__(self, schema, node):
        super(SimpleType, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.add_type_instance(self)
    
    @cached_property
    def name(self):
        name_attr = self.node.attrib.get('name')
        name_attr = (name_attr and name_attr[0]) or None
        return name_attr

    def _parse(self):
        self.content = None
        restriction_node = self.node.xpath(
            "xsd:restriction",
            namespaces=self.schema.nsmap
        )
        if restriction_node:
            restriction_node = restriction_node[0]
            self.content = SimpleTypeRestriction(
                self.schema, restriction_node)

        list_node = self.node.xpath(
            "xsd:restriction",
            namespaces=self.schema.nsmap
        )
        if list_node:
            self.content = List(self.schema, list_node[0])

        union_node = self.node.xpath(
            "xsd:union",
            namespaces=self.schema.nsmap
        )
        if union_node:
            self.content = Union(self.schema, union_node[0])
