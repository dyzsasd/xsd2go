from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value

from .base import Node
from .base_type import name2base_class
from .attribute_container import AttributeContainerMixin
from .element_container import ElementContainerMixin
from .type_decorator import Restriction


class ComplexType(Node, AttributeContainerMixin, ElementContainerMixin):
    def __init__(self, schema, node):
        super(ComplexType, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.add_type_instance(self)

    @cached_property
    def name(self):
        name_attr = self.node.xpath("@name")
        name_attr = (name_attr and name_attr[0]) or None
        return name_attr

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


class Extension(Node, AttributeContainerMixin, ElementContainerMixin):
    @cached_property
    def base_type_instance(self):
        type_name, type_ns = parse_ref_value(
            self.node.attrib['base'], self.schema.nsmap)
        if type_ns == self.schema.nsmap[XSD_NS]:
            return name2base_class[type_name]()
        else:
            refered_type_instance = self.schema.get_type_instance(
                type_name, type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance
    
    def _parse(self):
        self._parse_attributes()
        self._parse_elements()


class SimpleContentRestriction(Restriction, AttributeContainerMixin):
    def _parse(self):
        super(SimpleContentRestriction, self)._parse()
        self._parse_attributes()


class ComplexContentRestriction(Restriction, AttributeContainerMixin, ElementContainerMixin):
    def _parse(self):
        super(ComplexContentRestriction, self)._parse()
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
