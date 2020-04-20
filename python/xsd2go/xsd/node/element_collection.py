from cached_property import cached_property
from lxml import etree

from xsd2go.xsd.util import parse_ref_value, parse_tag
from .base import Node


def create_collection(schema, node, parent):
    tag, _ = parse_tag(node.tag)
    if tag == "group":
        return Group(schema, node, parent)
    elif tag == "all":
        return All(schema, node, parent)
    elif tag == "choice":
        return Choice(schema, node, parent)
    elif tag == "sequence":
        return Sequence(schema, node, parent)
    else:
        raise RuntimeError(
            "Cannot parse the collection node:\n%s" % etree.tostring(node).decode("utf8"))


class ElementCollection(Node):
    @cached_property
    def elements(self):
        elements = self.nested_elements
        for collection in self.collections:
            elements = elements + collection.elements
        return elements

    def _parse(self):
        from .element import Element

        self.nested_elements = [
            Element(self.schema, node, self, index)
            for index, node in enumerate(self.node.xpath(
                "xsd:element",
                namespaces=self.schema.nsmap
            ))
        ]
        self.collections = [
            create_collection(self.schema, node, self)
            for node in self.node.xpath(
                "*[self::xsd:group or self::xsd:all or self::xsd:choice or self::xsd:sequence]",
                namespaces=self.schema.nsmap
            )
        ]


class Group(ElementCollection):
    @cached_property
    def elements(self):
        if 'ref' in self.node.attrib:
            ref_name, ref_ns = self.parse_ref_value(
                self.node.attrib['ref'])
            refered_element_group = self.schema.get_element_group(
                ref_name, ref_ns)
            if refered_element_group is None:
                raise RuntimeError(
                    "Cannot find ref element group for %s" % self.tostring())
            else:
                return refered_element_group.elements
        return super(Group, self).elements


class All(ElementCollection):
    pass


class Choice(ElementCollection):
    pass


class Sequence(ElementCollection):
    pass
