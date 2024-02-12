import yaml
import json
import glob

class Trie:

    def __init__(self):
        self.children = {}
        self.values = []

    def insert(self, path, value):
        node = self
        for c in path:
            if c not in node.children:
                node.children[c] = Trie()
            node = node.children[c]
        node.values.append(value)

    def json(self):
        if not self.children:
            return self.values
        return {k: v.json() for k, v in self.children.items()}
    
    def tabulator_leaf(self):
        result = {}
        for v in self.values:
            result[v["format"]] = v["table_cell"]
        return result

    def tabulator(self):
        if not self.children:
            return []
        result = []
        for k, v in self.children.items():
            d = {
                "feature": k,
                **v.tabulator_leaf()
            }
            children = v.tabulator()
            if children:
                d["_children"] = children
            result.append(d)
        return result

    def depth(self):
        if not self.children:
            return 0
        return max([v.depth() for v in self.children.values()]) + 1

    def size(self):
        if not self.children:
            return 1
        return sum([v.size() for v in self.children.values()])


def extract_metadata_from_file(file):
    with open(file, "r") as f:
        lines = f.readlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if start is None:
                start = i
            else:
                end = i
                metadata = yaml.load("".join(lines[start+1:end]), Loader=yaml.SafeLoader)
                return metadata
    raise ValueError("No metadata found in file %s" % file)

def table_cell(entry, _feature, _format_name, _format_config):
    return "<a href='%s' target='_blank'><i class='fa-solid fa-link' aria-label='link'></i></a>" % entry

def render_features_formats_data():
    trie = Trie()
    for entry in glob.glob("qmd-files/**/document.qmd", recursive=True):
        feature = entry.split("/")[1:-1]
        front_matter = extract_metadata_from_file(entry)
        try:
            format = front_matter["format"]
        except KeyError:
            raise Exception("No format found in %s" % entry)
        for format_name, format_config in format.items():
            trie.insert(feature, {
                "feature": "/".join(feature),
                "format": format_name,
                "format_config": format_config,
                "table_cell": table_cell(entry, feature, format_name, format_config)
            })
    entries = trie.tabulator()

    return "```{=html}\n<script type='text/javascript'>\nvar tableData = %s;\n</script>\n```\n" % json.dumps(entries, indent=2)