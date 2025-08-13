import yaml


class TemplateError(Exception):
    """Base exception for template loading errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when template file is not found."""
    def __init__(self, template_path: str):
        super().__init__(f"Template file not found: {template_path}. Please check that the template file exists and the path is correct.")


class TemplateParseError(TemplateError):
    """Raised when template file cannot be parsed."""
    def __init__(self, template_path: str, original_error: str):
        super().__init__(f"Error parsing template file {template_path}: {original_error}. Please check that the template file is valid YAML.")


def load_template(template_file):
    try:
        with open(template_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise TemplateNotFoundError(template_file)
    except yaml.YAMLError as e:
        raise TemplateParseError(template_file, str(e))
    except Exception as e:
        raise TemplateParseError(template_file, str(e))
