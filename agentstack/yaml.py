from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString


__all__ = (
    'parser',
    'YAMLError', 
    'FoldedScalarString',
)

def _represent_none_as_tilde(self, data) -> None:
    return self.represent_scalar('tag:yaml.org,2002:null', '~')


parser: YAML = YAML()
parser.preserve_quotes = True  # Preserve quotes in existing data

# this affects all instances, so putting it here to make that obvious
parser.representer.add_representer(type(None), _represent_none_as_tilde)

