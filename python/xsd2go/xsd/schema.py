# Schema is a single xsd file

from cached_property import cached_property
from lxml import etree

from xsd2go.constants import XSD_NS

from .node.element import Element
from .node.attribute import Attribute
from .node.simple_type import SimpleType
from .node.complex_type import ComplexType
from .node.attribute_container import AttributeGroup
from .node.element_collection import Group


class Schema(object):
    def __init__(self, project, file_path):
        self.project = project
        self.file_path = file_path
        self.xml_tree = etree.parse(open(file_path))

        self.name2element = {}
        self.name2attribute = {}
        self.name2type_instance = {}
        self.name2attribute_group = {}
        self.name2element_group = {}

    def add_element(self, element):
        self.name2element[element.node.attrib['name']] = element

    def get_element(self, name, ns):
        element = self.name2element.get(name)
        if element is not None and not element.is_same_ns(ns):
            element = None
        
        if element is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project.schemas[schema_path]
                element = schema.get_element(name, ns)
                if element is not None and element.ns is not None and element.ns != ns:
                    element = None
        return element

    def add_type_instance(self, type_instance):
        if type_instance.node.attrib['name'] in self.name2type_instance:
            raise RuntimeError(
                "Duplicate type definition in %s" % self.file_path)
        self.name2type_instance[type_instance.node.attrib['name']] = type_instance

    def get_type_instance(self, name, ns):
        type_instance = self.name2type_instance.get(name)
        if type_instance is not None and not type_instance.is_same_ns(ns):
            type_instance = None
        if type_instance is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project.schemas[schema_path]
                type_instance = schema.get_type_instance(name, ns)
                if type_instance is not None and not type_instance.is_same_ns(ns):
                    type_instance = None
        return type_instance

    def add_attribute(self, attribute):
        if attribute.node.attrib['name'] in self.name2attribute:
            raise RuntimeError(
                "Duplicate attribute %s definition in %s",
                attribute.node.attrib['name'], self.file_path
            )
        self.name2attribute[attribute.node.attrib['name']] = attribute

    def get_attribute(self, name, ns):
        attribute = self.name2attribute.get(name)
        if attribute is not None and not attribute.is_same_ns(ns):
            attribute = None
        
        if attribute is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project.path2schema[schema_path]
                attribute = schema.get_attribute(name, ns)
                if attribute is not None and not attribute.is_same_ns(ns):
                    attribute = None
        return attribute

    def add_attribute_group(self, attribute_group):
        self.name2attribute_group[attribute_group.node.attrib['name']] = attribute_group

    def get_attribute_group(self, name, ns):
        attribute_group = self.name2attribute_group.get(name)
        if attribute_group is not None and not attribute_group.is_same_ns(ns):
            attribute_group = None

        if attribute_group is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project.path2schema[schema_path]
                attribute_group = schema.get_attribute_group(name, ns)
                if attribute_group is not None and not attribute_group.is_same_ns(ns):
                    attribute_group = None
        return attribute_group

    def get_element_group(self, name, ns):
        element_group = self.name2element_group.get(name)
        if element_group is not None and not element_group.is_same_ns(ns):
            element_group = None
        
        if element_group is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project.path2schema[schema_path]
                element_group = schema.get_element_group(name, ns)
                if element_group is not None and not element_group.is_same_ns(ns):
                    element_group = None
        return element_group

    @cached_property
    def root(self):
        return self.xml_tree.getroot()

    @cached_property
    def nsmap(self):
        nsmap = self.root.nsmap
        nsmap[XSD_NS] = "http://www.w3.org/2001/XMLSchema"
        if None in nsmap:
            nsmap["default"] = nsmap[None]
            nsmap.pop(None) 
        return nsmap
    
    @cached_property
    def target_ns(self):
        return self.root.attrib.get('targetNamespace')

    @cached_property
    def included_schema_paths(self):
        included_schema_paths = []
        for include in self.root.xpath("xsd:include", namespaces=self.nsmap):
            path = include.xpath("@schemaLocation")[0]
            included_schema_paths.append(path)
        return included_schema_paths

    @cached_property
    def imported_schema_paths(self):
        imported_schema_paths = []
        for _import in self.root.xpath("xsd:import", namespaces=self.nsmap):
            path = _import.xpath("@schemaLocation")[0]
            imported_schema_paths.append(path)
        return imported_schema_paths

    def load(self):
        self.schema_element_collection = [
            Element(self, node)
            for node in self.root.xpath("xsd:element", namespaces=self.nsmap)
        ]
        self.schema_attribute_collection = [
            Attribute(self, node)
            for node in self.root.xpath("xsd:attribute", namespaces=self.nsmap)
        ]

        for node in self.root.xpath('xsd:simpleType', namespaces=self.nsmap):
            SimpleType(self, node)

        for node in self.root.xpath('xsd:complexType', namespaces=self.nsmap):
            ComplexType(self, node)

        for node in self.root.xpath('xsd:attributeGroup', namespaces=self.nsmap):
            AttributeGroup(self, node)

        for node in self.root.xpath('xsd:group', namespaces=self.nsmap):
            Group(self, node)

        return self
