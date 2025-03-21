from typing import Dict

end_case = "__end__"


def build_tree(key_words) -> Dict[str, str]:
    root = {}
    for word in key_words:
        current = root
        for char in word:
            if char not in current:
                current[char] = {}
            current = current[char]
        current[end_case] = end_case
    return root


def search_tree(tree: Dict[str, str], text: str):
    depth = tree
    for char in text:
        depth = depth[char]

    while True:
        keys = depth.keys()
        key = next(iter(keys))
        if key == end_case:
            yield text + " "
            break
        text += key
        depth = depth[key]
    return None


def dfs(tree: Dict[str, str], curr: str):
    for child_key in tree.keys():
        if child_key == end_case:
            yield curr
            break
        yield from dfs(tree[child_key], curr + child_key)


def all_options(tree: Dict[str, str], text: str):
    depth = tree
    for char in text:
        depth = depth[char]
    all_combinations = []
    for key in depth.keys():
        all_combinations.extend(dfs(depth[key], key))

    return " ".join(f"{text}{elem}" for elem in all_combinations)
