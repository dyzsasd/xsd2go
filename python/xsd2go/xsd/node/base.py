from cached_property import cached_property
from lxml import etree

from xsd2go.xsd.util import parse_attrib_value, parse_tag


class Node(object):
    def __init__(self, schema, node, parent):
        self.schema = schema
        self.node = node
        self.parent = parent
        self._parse()

    @cached_property
    def node_id(self):
        _id = self.node.tag
        if self.name is not None:
            _id = _id + "-" + self.name
        if self.parent is None:
            return "/" + _id
        elif self.name is None:
            return self.parent + "/" + _id

    @cached_property
    def name(self):
        return None
    
    @cached_property
    def prefix(self):
        if self.parent is not None:
            return self.parent.prefix
        else:
            return ""
    
    def go_package_name(self):
        return self.schema.go_package_name()
    
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
