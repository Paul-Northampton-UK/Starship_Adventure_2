import sys
from copy import deepcopy
from pathlib import Path

from ruamel.yaml import YAML


def main() -> None:
    objects_path = Path('data/objects.yaml')
    backup_path = Path('data/objects.backup.yaml')

    # Backup current file
    backup_path.write_text(objects_path.read_text(encoding='utf-8'), encoding='utf-8')

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=2)

    with objects_path.open('r', encoding='utf-8') as f:
        root = yaml.load(f)

    # Determine where the objects list is stored
    if isinstance(root, dict) and isinstance(root.get('objects'), list):
        objects_list = root['objects']
        root_is_mapping = True
    elif isinstance(root, list):
        objects_list = root
        root_is_mapping = False
    else:
        print('Unrecognized objects.yaml structure; aborting to be safe.')
        sys.exit(1)

    keys_to_always_keep = {"id", "name", "location", "area_location", "category"}
    # Keys where mere presence/particular values change behavior
    presence_sensitive_base = {
        "initial_state",   # keep only if False (hidden)
        "is_open",         # keep only if True (initially open)
        "lock_type",       # presence implies lockable
        "lock_details",
        "lock_key_id",
        "is_locked",       # keep only if True
    }

    def is_empty(value) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False

    def clean_properties(props: dict) -> dict:
        if not isinstance(props, dict):
            return {}
        cleaned: dict = {}
        for k, v in props.items():
            if isinstance(v, bool):
                if v:
                    cleaned[k] = True
                continue
            if isinstance(v, (int, float)):
                cleaned[k] = v
                continue
            if not is_empty(v):
                cleaned[k] = v
        return cleaned

    def clean_base(obj: dict) -> dict:
        obj = deepcopy(obj)
        for k in list(obj.keys()):
            v = obj.get(k)
            if k in keys_to_always_keep:
                continue
            if k in presence_sensitive_base:
                if k == "initial_state":
                    # Keep only if explicitly False (hidden)
                    if v is False:
                        continue
                    else:
                        obj.pop(k, None)
                        continue
                if k == "is_open":
                    # Keep only if True
                    if v is True:
                        continue
                    else:
                        obj.pop(k, None)
                        continue
                if k in {"lock_type", "lock_details", "lock_key_id"}:
                    # Keep if non-empty; presence matters
                    if not is_empty(v):
                        continue
                    else:
                        obj.pop(k, None)
                        continue
                if k == "is_locked":
                    # Keep only if True
                    if v is True:
                        continue
                    else:
                        obj.pop(k, None)
                        continue
            # Generic pruning
            if isinstance(v, bool):
                if not v:
                    obj.pop(k, None)
                    continue
            elif is_empty(v):
                obj.pop(k, None)
                continue

        # Clean properties subtree
        if isinstance(obj.get("properties"), dict):
            obj["properties"] = clean_properties(obj["properties"])
            if not obj["properties"]:
                obj.pop("properties", None)

        # Clean synonyms list to remove empties; drop if becomes empty
        if isinstance(obj.get("synonyms"), list):
            syn = [str(s).strip() for s in obj["synonyms"] if str(s).strip()]
            if syn:
                obj["synonyms"] = syn
            else:
                obj.pop("synonyms", None)

        return obj

    cleaned_objects = []
    for entry in objects_list:
        if not isinstance(entry, dict):
            cleaned_objects.append(entry)
            continue
        cleaned_objects.append(clean_base(entry))

    if root_is_mapping:
        root['objects'] = cleaned_objects
    else:
        root = cleaned_objects

    with objects_path.open('w', encoding='utf-8') as f:
        yaml.dump(root, f)

    print('Normalized data/objects.yaml and wrote backup to data/objects.backup.yaml')


if __name__ == '__main__':
    main()



