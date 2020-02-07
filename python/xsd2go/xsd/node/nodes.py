from cached_property import cached_property
from lxml import etree

from xsd2go.constants import XSD_NS
from xsd2go.xsd.type import name2base_class
from xsd2go.xsd.util import parse_attrib_value, parse_tag, parse_ref_value

from .base import Node


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

    def _parse(self):
        self.nested_type = None

        simple_type_node = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_node:
            self.nested_type = SimpleType(self.schema, simple_type_node[0])


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
            "Cannot parse the collection node:\n%s" % etree.tostring(node).decode("utf8"))


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


class Element(Node):
    def __init__(self, schema, node):
        super(Element, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.name2element[self.node.attrib['name']] = self

    @cached_property
    def name(self):
        _name = self.node.attrib.get('name')

        if _name is None and self.ref_element is not None:
            _name = self.ref_element.name

        if _name is None:
            raise RuntimeError(
                "Cannot get name from %s" % self.tostring())
        return _name

    @cached_property
    def ref_element(self):
        ref = self.node.attrib.get('ref')
        if ref is not None:
            ref_element = self.schema.get_element(ref)
            if ref_element is None:
                raise RuntimeError(
                    "Cannot find ref element for %s" % self.tostring())
            return ref_element
        return None

    @cached_property
    def type_instance(self):
        if self.nested_type is not None:
            return self.nested_type
        elif self.ref_element is not None:
            return self.ref_element.type_instance
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

    @property
    def max_occrs(self):
        return self.node.attrib.get("maxOccurs", "1")

    @property
    def min_occrs(self):
        return self.node.attrib.get("minOccurs", "1")

    @property
    def is_list(self):
        return self.max_occrs != "1"

    def _parse(self):
        self.nested_type = None

        simple_type_node = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_node:
            self.nested_type = SimpleType(self.schema, simple_type_node[0])

        complex_type_node = self.node.xpath(
            "xsd:complexType",
            namespaces=self.schema.nsmap
        )

        if complex_type_node:
            self.nested_type = ComplexType(self.schema, complex_type_node[0])


class TypeDecorator(Node):
    def wrapped_type(self):
        raise NotImplementedError(
            "Method `wrapped_type` isn't implemented in class %s" % self.__class__)

    def _parse(self):
        self.nested_type = None
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_nodes:
            self.nested_type = SimpleType(self.schema, simple_type_nodes[0])


class Restriction(TypeDecorator):
    @cached_property
    def wrapped_type(self):
        if self.nested_type is not None:
            return self.nested_type

        base_type_name, base_type_ns = parse_ref_value(
            self.node.attrib['base'], self.schema.nsmap)
        if base_type_ns == self.schema.nsmap[XSD_NS]:
            return name2base_class[base_type_name]()
        else:
            refered_type_instance = self.schema.get_type_instance(
                base_type_name, base_type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance
        

class SimpleTypeRestriction(Restriction):
    "Restriction element nested in simple type"
    
    @cached_property
    def restrictions(self):
        kwargs = {}
        enum = []
        for item in self.node:
            ns, tag = parse_tag(item.tag)
            if ns != self.schema.nsmap['xsd']:
                raise RuntimeError(
                    "cannot parse restriction item %s", self.tostring())
            if tag == "enumeration":
                enum.append(item.attrib["value"])
                continue
            kwargs[tag] = item.attrib["value"]

        if enum:
            kwargs['enumeration'] = enum

        return kwargs


class List(TypeDecorator):
    @cached_property
    def wrapped_type(self):
        if self.nested_type is not None:
            return self.nested_type
        else:
            type_name, type_ns = parse_ref_value(
                self.node.attrib['itemType'], self.schema.nsmap)
            refered_type_instance = self.schema.get_type_instance(
                type_name, type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance


class Union(Node):
    @cached_property
    def member_types(self):
        if self.nested_types:
            return self.nested_types
        else:
            member_type_names = self.node.attrib['memberTypes'].split(" ")
            _member_type_instances = []
            for _name in member_type_names:
                type_name, type_ns = parse_ref_value(
                    self.node.attrib['itemType'], self.schema.nsmap)
                refered_type_instance = self.schema.get_type_instance(
                    type_name, type_ns)
                if refered_type_instance is None:
                    raise RuntimeError(
                        "Cannot find ref type for %s" % self.tostring())
                else:
                    _member_type_instances.append(refered_type_instance)
            return _member_type_instances

    def _parse(self):
        self.nested_types = []
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        for type_node in simple_type_nodes:
            self.nested_types.append(
                SimpleType(self.schema, type_node))


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
        super(SimpleContentRestriction, self)._parse(self)
        self._parse_attributes()


class ComplexContentRestriction(Restriction, AttributeContainerMixin, ElementContainerMixin):
    def _parse(self):
        super(ComplexContentRestriction, self)._parse(self)
        self._parse_attributes()
        self._parse_elements()


class TypeNode(Node):
    def __init__(self, schema, node):
        super(TypeNode, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            if self.node.attrib['name'] in self.schema.name2type_instance:
                raise RuntimeError("Duplicate type definition in %s" % schema.path)
            self.schema.name2type_instance[self.node.attrib['name']] = self
    
    @cached_property
    def name(self):
        raise NotImplementedError("Method name has not been implemented in %s" % self.__class__.__name__)


class SimpleType(TypeNode):
    @cached_property
    def name(self):
        name_attr = self.node.xpath("@name")
        name_attr = (name_attr and name_attr[0]) or None
        return name_attr

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
