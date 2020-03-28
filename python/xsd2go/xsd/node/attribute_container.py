from cached_property import cached_property

from xsd2go.xsd.util import parse_ref_value

from .base import Node


class AttributeContainerMixin(object):
    @cached_property
    def attributes(self):
        _attributes = self.nested_attributes
        for _group in self.nested_attribute_groups:
            _attributes = _attributes + _group.attributes
        return _attributes

    def _parse_attributes(self):
        from .attribute import Attribute

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
            self.schema.add_attribute_group(self)
    
    @cached_property
    def attributes(self):
        if 'ref' in self.node.attrib:
            ref_name, ref_ns = self.parse_ref_value(
                self.node.attrib['ref'])
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
