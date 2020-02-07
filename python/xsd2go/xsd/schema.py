from os.path import join as path_join
import re

from cached_property import cached_property
from lxml import etree

from xsd2go.constants import XSD_NS

from .node.nodes import Attribute, AttributeGroup
from .node.nodes import Element
from .node.nodes import Group
from .node.nodes import SimpleType, ComplexType
from .util import parse_tag, parse_ref_value


class ProjectContext(object):
    def __init__(self, base_path):
        self.path2schema = {}
        self.base_path = base_path

    def get_schema(self, path):
        return self.path2schema.get(path)

    def load_schema(self, xsd_file):
        filepath = path_join(self.base_path, xsd_file)
        xml_tree = etree.parse(open(filepath))

        schema = Schema(filepath, self, xml_tree)

        for path in schema.included_schema_paths + schema.imported_schema_paths:
            if path not in self.path2schema:
                self.load_schema(path)
        
        self.path2schema[xsd_file] = schema
        return schema


class Schema(object):
    def __init__(self, path, project_context, xml_tree):
        self.path = path
        self.project_context = project_context
        self.xml_tree = xml_tree

        self._parse()

    @cached_property
    def root(self):
        return self.xml_tree.getroot()

    @cached_property
    def nsmap(self):
        nsmap = self.root.nsmap
        nsmap[XSD_NS] = "http://www.w3.org/2001/XMLSchema"
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

    def get_element(self, name, ns):
        element = self.name2element.get(name)
        if element is not None and not element.is_same_ns(ns):
            element = None
        
        if element is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project_context.path2schema[schema_path]
                element = schema.get_element(name, ns)
                if element is not None and element.ns is not None and element.ns != ns:
                    element = None
        return element

    def get_attribute(self, name, ns):
        attribute = self.name2attribute.get(name)
        if attribute is not None and not attribute.is_same_ns(ns):
            attribute = None
        
        if attribute is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project_context.path2schema[schema_path]
                attribute = schema.get_attribute(name, ns)
                if attribute is not None and not attribute.is_same_ns(ns):
                    attribute = None
        return attribute

    def get_type_instance(self, name, ns):
        type_instance = self.name2type_instance.get(name)
        if type_instance is not None and not type_instance.is_same_ns(ns):
            type_instance = None
        if type_instance is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project_context.path2schema[schema_path]
                type_instance = schema.get_type_instance(name, ns)
                if type_instance is not None and not type_instance.is_same_ns(ns):
                    type_instance = None
        return type_instance

    def get_attribute_group(self, name, ns):
        attribute_group = self.name2attribute_group.get(name)
        if attribute_group is not None and not attribute_group.is_same_ns(ns):
            attribute_group = None
        
        if attribute_group is None:
            for schema_path in self.included_schema_paths + self.imported_schema_paths:
                schema = self.project_context.path2schema[schema_path]
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
                schema = self.project_context.path2schema[schema_path]
                element_group = schema.get_element_group(name, ns)
                if element_group is not None and not element_group.is_same_ns(ns):
                    element_group = None
        return element_group

    def _parse(self):
        self.name2element = {}
        self.name2attribute = {}
        self.name2type_instance = {}
        self.name2attribute_group = {}
        self.name2element_group = {}

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
