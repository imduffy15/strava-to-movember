import yaml


def yamlify(doc):
    return yaml.safe_dump(doc, default_flow_style=False)
