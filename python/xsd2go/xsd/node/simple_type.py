from cached_property import cached_property

from xsd2go.xsd.util import parse_ref_value, parse_tag
from xsd2go.constants import XSD_NS

from xsd2go.xsd_go_type import xsd2go_type
from .base import Node
from .type_decorator import SimpleTypeRestriction, List, Union


class SimpleType(Node):
    def __init__(self, schema, node, parent):
        super(SimpleType, self).__init__(schema, node, parent)
        if 'name' in self.node.attrib:
            self.schema.add_type_instance(self)
    
    @cached_property
    def name(self):
        name_attr = self.node.attrib.get('name')
        name_attr = (name_attr and name_attr[0]) or None
        return name_attr

    def go_type_name(self):
        if self.content is None:
            raise RuntimeError(
                "SimpleType %s's def is empty", self.name)
        return self.content.go_type_name()

    def go_struct_attributes(self):
        return []

    def _parse(self):
        self.content = None
        restriction_node = self.node.xpath(
            "xsd:restriction",
            namespaces=self.schema.nsmap
        )
        if restriction_node:
            restriction_node = restriction_node[0]
            self.content = SimpleTypeRestriction(
                self.schema, restriction_node, self)

        list_node = self.node.xpath(
            "xsd:list",
            namespaces=self.schema.nsmap
        )
        if list_node:
            self.content = List(self.schema, list_node[0], self)

        union_node = self.node.xpath(
            "xsd:union",
            namespaces=self.schema.nsmap
        )
        if union_node:
            self.content = Union(self.schema, union_node[0], self)

    def go_struct_def(self):
        return None

    def export_go_struct(self, base_class, base_module):
        return