try:
    import importlib.util
    import os
    chord_trie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "chord_trie.py"))
    spec = importlib.util.spec_from_file_location("chord_trie", chord_trie_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load chord_trie.py from {chord_trie_path}")
    chord_trie = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chord_trie)
    print("chord_trie.py imported successfully.")
except Exception as e:
    print(f"Error importing chord_trie.py: {e}")
