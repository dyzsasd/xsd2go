import argparse
import os

from xsd2go.xsd.project import Project


parser = argparse.ArgumentParser()
parser.add_argument("path", type=str, help="XSD file repo path")
parser.add_argument(
    "--package", type=str, default="xsd",
    help="Go package name"
)
parser.add_argument(
    "--output", type=str, default="go",
    help="output dir of go script"
)
parser.add_argument(
    "--schemas", type=str, nargs='*',
    help="XSD schemas for output"
)
parser.add_argument(
    "--recursive", default=False, action="store_true",
    help="Register all classes even it is not directly attached to root node"
)


if __name__ == "__main__":
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    p = Project(args.path)
    p.load_schema(args.output, args.package, recursive=args.recursive)

    output_schemas = args.schemas or list(p.schemas.keys())

    for name in output_schemas:
        s = p.schemas.get(name)
        if s is None:
            raise RuntimeError("Cannot find xsd file of %s", name)
        for name, type_instance in s.name2type_instance.items():
            type_instance.export_go_struct()
        for element in s.element_collection:
            if element.nested_type is not None:
                element.nested_type.export_go_struct(
                    element.name + 'Type')


