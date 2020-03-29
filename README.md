# Install

Requires:
  - python > 3.6
  - pip > 19.0.0 

```bash
pip install -r requirements.txt
```

# Usage:

## Help:

```bash
PYTHONPATH=python python3 -m xsd2go.main -h
```

## Generate Go Structs

```bash
PYTHONPATH=python/ python -m xsd2go.main <xsd file dir> --package <go package> --output <output dir> [--schemas xsd_file [xsd_file]]
```

