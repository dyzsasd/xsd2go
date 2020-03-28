from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value, parse_tag
from xsd2go.xsd_go_type import xsd2go_type

from .base import Node
from .simple_type import SimpleType

class Attribute(Node):
    def __init__(self, schema, node):
        super(Attribute, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.add_attribute(self)

    @cached_property
    def name(self):
        _name = self.node.attrib.get('name')

        if _name is None and self.ref_attribute is not None:
            _name = self.ref_attribute.name
        
        if _name is None:
            raise RuntimeError(
                "Cannot get name from %s" % self.tostring())
        return _name

    @cached_property
    def ref_attribute(self):
        ref = self.node.attrib.get('ref')
        if ref is not None:
            ref_attribute = self.schema.get_attribute(ref)
            if ref_attribute is None:
                raise RuntimeError(
                    "Cannot find ref attribute for %s" % self.tostring())
            return ref_attribute
        return None

    @cached_property
    def type_instance(self):
        if self.nested_type is not None:
            return self.nested_type
        elif self.ref_attribute is not None:
            return self.ref_attribute.type_instance
        else:
            type_name, type_ns = self.parse_ref_value(
                self.node.attrib['type'])
            refered_type_instance = self.schema.get_type_instance(
                type_name, type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance

    def _parse(self):
        self.nested_type = None

        simple_type_node = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_node:
            self.nested_type = SimpleType(self.schema, simple_type_node[0])

    def to_string(self):
        if self.nested_type is None and self.ref_attribute is None and 'type' not in self.node.attrib:
            return None

        type_name, type_ns = self.parse_ref_value(
                self.node.attrib['type'])

        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['type']
                )
        else:
            go_struct_name = self.type_instance.go_struct_name()
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find type name for %s", self.node.attrib['type'])
        
        return '{field} {type} `xml:"{xml_field},attr"`;'.format(**{
            "field": self.name,
            "type": go_struct_name,
            "xml_field": self.name
        })