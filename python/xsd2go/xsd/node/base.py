from cached_property import cached_property
from lxml import etree

from xsd2go.xsd.util import parse_attrib_value


class Node(object):
    def __init__(self, schema, node):
        self.schema = schema
        self.node = node
        self._parse()
    
    def parse_ref_value(self, value):
        if not value:
            return None, None
        name, ns_tag = parse_attrib_value(value)
        return name, self.node.nsmap.get(ns_tag)

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

    def export(self, default_name, **kwargs):
        raise NotImplementedError(
            "Method `export` isn't implemented in class %s" % self.__class__)

    def _parse(self):
        raise NotImplementedError(
            "Method `_parse` isn't implemented in class %s" % self.__class__)
