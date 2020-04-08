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
PYTHONPATH=python/ python -m xsd2go.main aa_xsd/ --base-path <output dir> --base-module <project module>
```

