from os.path import join as path_join
import re

from lxml import etree

from .models.context import XSDProject, Schema
from .models.type import ComplexType, name2base_class
from .models.element import Element
from .models.parse_node import (
    parse_type_node, parse_element_container,
    parse_element_node, parse_attribute_group
)

def parse_xsd_files(files, base_path=""):
    project = XSDProject(base_path)

    for xsd_file in files:
        schema = project.load_schema(xsd_file)
        parse_schema(schema)
    return project


def parse_schema(schema):
    elements = schema.get_elements()

    return elements


if __name__ == "__main__":
    parse_xsd_files(["AirShoppingRQ.xsd"], base_path="test")
