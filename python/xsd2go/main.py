from xsd2go.xsd.project import Project


if __name__ == "__main__":
    p = Project("af_xsd/AirShopping")
    p.load_schema()
