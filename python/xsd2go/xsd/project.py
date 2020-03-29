# XSD project contains all schema files
import glob
from os.path import join, relpath

from .schema import Schema


class Project(object):
    def __init__(self, path):
        self.path = path
        self.schemas = {}

    def load_schema(self, output_dir, package, recursive=False):
        xsd_files = glob.glob(
            join(self.path, "*.xsd"), recursive=True)
        for f in xsd_files:
            if f not in self.schemas:
                print('loading %s' % f)
                rel_path = relpath(f, self.path)
                self.schemas[rel_path] = Schema(
                    self, f, output_dir,
                    package, recursive=recursive
                ).load()
