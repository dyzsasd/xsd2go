from cached_property import cached_property

from xsd2go.xsd.util import parse_ref_value

from .base import Node
from .type import SimpleType


class AttributeContainerMixin(object):
    @cached_property
    def attributes(self):
        _attributes = self.nested_attributes
        for _group in self.nested_attribute_groups:
            _attributes = _attributes + _group.attributes
        return _attributes

    def _parse_attributes(self):
        attribute_nodes = self.node.xpath(
            "xsd:attribute",
            namespaces=self.schema.nsmap
        )
        self.nested_attributes = [
            Attribute(self.schema, node)
            for node in attribute_nodes
        ]

        attribute_group_nodes = self.node.xpath(
            "xsd:attributeGroup",
            namespaces=self.schema.nsmap
        )
        self.nested_attribute_groups = [
            AttributeGroup(self.schema, node)
            for node in attribute_group_nodes
        ]


class AttributeGroup(Node, AttributeContainerMixin):
    def __init__(self, schema, node):
        super(AttributeGroup, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.name2attribute_group[self.node.attrib['name']] = self
    
    @cached_property
    def attributes(self):
        if 'ref' in self.node.attrib:
            ref_name, ref_ns = parse_ref_value(
                self.node.attrib['ref'], self.schema.nsmap)
            refered_attribute_group = self.schema.get_attribute_group(
                ref_name, ref_ns)
            if refered_attribute_group is None:
                raise RuntimeError(
                    "Cannot find ref attribute group for %s" % self.tostring())
            else:
                return refered_attribute_group.attributes

        return super(AttributeGroup, self).attributes


    def _parse(self):
        self._parse_attributes()


class Attribute(Node):
    def __init__(self, schema, node):
        super(Attribute, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.name2attribute[self.node.attrib['name']] = self

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
            type_name, type_ns = parse_ref_value(
                self.node.attrib['type'], self.schema.nsmap)
            refered_type_instance = self.schema.get_type_instance(
                type_name, type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance

    def _parse(self, schema):
        self.nested_type = None

        simple_type_node = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_node:
            self.nested_type = SimpleType(self.schema, simple_type_node[0])

