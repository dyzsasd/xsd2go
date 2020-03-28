# XSD project contains all schema files
import glob
from os.path import join, relpath

from .schema import Schema


class Project(object):
    def __init__(self, path):
        self.path = path
        self.schemas = {}

    def load_schema(self):
        xsd_files = glob.glob(
            join(self.path, "*.xsd"), recursive=True)
        for f in xsd_files:
            if f not in self.schemas:
                print('loading %s' % f)
                rel_path = relpath(f, self.path)
                self.schemas[rel_path] = Schema(self, f, 'go', 'airshopping').load()
        s = self.schemas['IATA_AirShoppingRQ.xsd']

        for e in s.element_collection:
            print(e.type_instance.export_go_struct())
