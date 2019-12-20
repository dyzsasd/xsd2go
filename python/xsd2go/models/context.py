from os.path import join as path_join
import re

from lxml import etree

from .parse_node import (
    parse_type_node, parse_element_container,
    parse_element_node, parse_attribute_group
)
from .util import parse_tag, parse_value


class XSDProject(object):
    def __init__(self, base_path):
        self.path2schema = {}
        self.base_path = base_path

    def get_schema(self, path):
        return self.path2schema.get(path)

    def load_schema(self, xsd_file):
        filepath = path_join(self.base_path, xsd_file)
        schema_root = etree.parse(open(filepath)).getroot()
        
        nsmap = schema_root.nsmap
        nsmap["xsd"] = "http://www.w3.org/2001/XMLSchema"
        target_ns = schema_root.attrib.get('targetNamespace')

        included_schemas = []
        for include in schema_root.xpath("xsd:include", namespaces=nsmap):
            path = include.xpath("@schemaLocation")[0]
            included_schema = self.path2schema.get(path)
            if included_schema is None:
                included_schema = self.load_schema(path)
            included_schemas.append(included_schema)
        
        imported_schemas = []
        for _import in schema_root.xpath("xsd:import", namespaces=nsmap):
            path = _import.xpath("@schemaLocation")[0]
            imported_schema = self.path2schema.get(path)
            if imported_schema is None:
                imported_schema = self.load_schema(path)
            imported_schemas.append(imported_schema)

        schema = Schema(
            self, schema_root, included_schemas, imported_schemas,
            nsmap=nsmap, target_ns=target_ns)
        self.path2schema[xsd_file] = schema
        return schema


class Schema(object):
    def __init__(self, project, root, included_schemas, imported_schemas,
                 nsmap=None, target_ns=None):
        self.project = project
        self.root = root
        self.included_schemas = included_schemas
        self.imported_schemas = imported_schemas

        self.is_parsed = False

        self.nsmap = nsmap or {}
        self.target_ns = target_ns

        self.name2element = {}
        self.name2type = {}
        self.name2attribute_group = {}
        self.name2element_group = {}
        self.schema_elements = []
    
    def get_element(self, name):
        ns, tag = parse_tag(name)
        ns = (ns and self.nsmap[ns]) or ""

        element = self.name2element.get(tag)
        if element is not None and element.ns != ns:
            element = None
        for schema in self.included_schemas + self.imported_schemas:
            if element is not None:
                break
            element = schema.get_element(tag)
            if element is not None and element.ns != ns:
                element = None
        return element

    def get_type_instance(self, name):
        ns_tag, tag = parse_value(name)
        ns = (ns_tag and self.nsmap[ns_tag]) or ""

        type_instance = self.name2type.get(tag)
        if type_instance is not None and type_instance.ns != ns:
            type_instance = None
        for schema in self.included_schemas + self.imported_schemas:
            if type_instance is not None:
                break
            type_instance = schema.get_type_instance(tag)
            if type_instance is not None and type_instance.ns != ns:
                type_instance = None
        return type_instance

    def get_attribute_group(self, name):
        ns, tag = parse_tag(name)
        ns = (ns and self.nsmap[ns]) or ""

        attribute_group = self.name2attribute_group.get(tag)
        for schema in self.included_schemas + self.imported_schemas:
            if attribute_group is not None:
                break
            attribute_group = schema.get_attribute_group(tag)
        return attribute_group

    def get_element_group(self, name):
        ns, tag = parse_tag(name)
        ns = (ns and self.nsmap[ns]) or ""

        element_group = self.name2element_group.get(tag)
        for schema in self.included_schemas + self.imported_schemas:
            if element_group is not None:
                break
            element_group = schema.get_element_group(tag)
        return element_group

    def get_elements(self):
        if not self.is_parsed:
            self.parse()
        return self.schema_elements

    def parse(self):
        elements = []

        for included_schema in self.included_schemas:
            included_schema.parse()

        for imported_schema in self.imported_schemas:
            imported_elements = imported_schema.get_elements()
            elements.extend(imported_elements)

        for node in self.root.xpath("xsd:attributeGroup", namespaces=self.nsmap):
            parse_attribute_group(self, node)
        
        type_nodes = self.root.xpath(
            'xsd:simpleType', namespaces=self.nsmap
        ) + self.root.xpath(
            'xsd:complexType', namespaces=self.nsmap
        )
        
        for type_node in type_nodes:
            type_instance = parse_type_node(self, type_node, None)
        
        elements = parse_element_container(self, self.root)

