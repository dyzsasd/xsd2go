from os.path import join as path_join
import re

from lxml import etree

from .xsd.schema import ProjectContext, Schema


def parse_xsd_files(files, base_path=""):
    project = ProjectContext(base_path)

    for xsd_file in files:
        schema = project.load_schema(xsd_file)
        for el in schema.schema_element_collection:
            if el.name == "AirShoppingRQ":
                type_instance = el.type_instance
                print(type_instance.name)

    return project


if __name__ == "__main__":
    parse_xsd_files(["AirShoppingRQ.xsd"], base_path="test")
