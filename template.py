import yaml

def load_template(template_file):
    with open(template_file, 'r') as f:
        return yaml.safe_load(f)
