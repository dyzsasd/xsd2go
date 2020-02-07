from cached_property import cached_property
from lxml import etree

from xsd2go.xsd.util import parse_tag, parse_ref_value

from .base import Node
from .element import Element


def create_collection(schema, node):
    tag, _ = parse_tag(node.tag)
    if tag == "group":
        return Group(schema, node)
    elif tag == "all":
        return All(schema, node)
    elif tag == "choice":
        return Choice(schema, node)
    elif tag == "sequence":
        return Sequence(schema, node)
    else:
        raise RuntimeError(
            "Cannot parse the collectio node:\n%s" % etree.tostring(node).decode("utf8"))


class ElementContainerMixin(object):
    def _parse_elements(self):
        self.element_collection = None

        collection_nodes = self.node.xpath(
            "*[self::xsd:group or self::xsd:all or self::xsd:choice or self::xsd:sequence]",
            namespaces=self.schema.nsmap
        )
        if collection_nodes:
            self.element_collection = create_collection(self.schema, collection_nodes[0])

        if self.element_collection is None:
            # By default, the indicator is Sequence
            self.indicator = Sequence(self.schema, self.node)


class ElementCollection(Node):
    @cached_property
    def elements(self):
        elements = self.nested_elements
        for collection in self.collections:
            elements = elements + collection.elements
        return elements

    def _parse(self):
        self.nested_elements = [
            Element(self.schema, node)
            for node in self.node.xpath(
                "xsd:element",
                namespaces=self.schema.nsmap
            )
        ]
        self.collections = [
            Element(self.schema, node)
            for node in self.node.xpath(
                "*[self::xsd:group or self::xsd:all or self::xsd:choice or self::xsd:sequence]",
                namespaces=self.schema.nsmap
            )
        ]


class Group(ElementCollection):
    @cached_property
    def elements(self):
        if 'ref' in self.node.attrib:
            ref_name, ref_ns = parse_ref_value(
                self.node.attrib['ref'], self.schema.nsmap)
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
        