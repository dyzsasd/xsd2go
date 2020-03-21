# XSD project contains all schema files
import glob
from os.path import join, relpath

from .schema import Schema


class Project(object):
    def __init__(self, path):
        self.path = path
        self.schema = {}

    def load_schema(self):
        xsd_files = glob.glob(
            join(self.path, "*.xsd"), recursive=True)
        for f in xsd_files:
            if f not in self.schema:
                print('loading %s' % f)
                rel_path = relpath(f, self.path)
                self.schema[rel_path] = Schema(self, f).load()
        s = self.schema['AirShoppingRQ.xsd']

        for e in s.schema_element_collection:
            print(e.name)
