from cached_property import cached_property
from lxml import etree

from xsd2go.constants import XSD_NS

from xsd2go.xsd.type import name2base_class
from xsd2go.xsd.util import parse_attrib_value, parse_tag, parse_ref_value


class Node(object):
    def __init__(self, schema, node):
        self.schema = schema
        self.node = node
        self._parse()

    def is_same_ns(self, ns):
        if self.schema.target_ns is None:
            return ns is None or ns == ""
        return self.schema.target_ns == ns

    def tostring(self):
        return etree.tostring(self.node).decode("utf8")
    
    @cached_property
    def docs(self):
        return self.node.xpath(
            "xsd:annotation/xsd:documentation/text()",
            namespaces=self.schema.nsmap
        )

    def _parse(self):
        raise NotImplementedError(
            "Method `parse` isn't implemented in class %s" % self.__class__)
