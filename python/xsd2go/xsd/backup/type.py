from .base import Node
from .attribute import AttributeContainerMixin
from .element_collection import  ElementContainerMixin
from .type_decorator import (
    Extension, ComplexContentRestriction, SimpleContentRestriction,
    SimpleTypeRestriction, List, Union
)


class TypeNode(Node):
    def __init__(self, schema, node):
        super(TypeNode, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.name2type_instance[self.node.attrib['name']] = self


class SimpleType(TypeNode):
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


class ComplexType(TypeNode, AttributeContainerMixin, ElementContainerMixin):
    def _parse(self):
        self.content = None

        simple_content = self.node.xpath(
            "xsd:simpleContent",
            namespaces=self.schema.nsmap
        )
        if simple_content:
            simple_content = simple_content[0]
            self.content = SimpleContent(self.schema, simple_content)

        complex_content = self.node.xpath(
            "xsd:complexContent",
            namespaces=self.schema.nsmap
        )
        if complex_content:
            complex_content = complex_content[0]
            self.content = ComplexContent(self.schema, complex_content)

        if self.content is None:
            self._parse_attributes()
            self._parse_elements()



class Content(Node):
    pass


class SimpleContent(Content):
    def _parse(self):
        self.decorator = None

        extensions = self.node.xpath(
            "xsd:extension", namespaces=self.schema.nsmap)
        if extensions:
            self.decorator = Extension(self.schema, extensions[0])

        restrictions = self.node.xpath(
            "xsd:restriction", namespaces=self.schema.nsmap)
        if restrictions:
            self.decorator = SimpleContentRestriction(
                self.schema, restrictions[0])


class ComplexContent(Content):
    def _parse(self):
        self.decorator = None

        extensions = self.node.xpath(
            "xsd:extension", namespaces=self.schema.nsmap)
        if extensions:
            self.decorator = Extension(self.schema, extensions[0])

        restrictions = self.node.xpath(
            "xsd:restriction", namespaces=self.schema.nsmap)
        if restrictions:
            self.decorator = ComplexContentRestriction(
                self.schema, restrictions[0])
