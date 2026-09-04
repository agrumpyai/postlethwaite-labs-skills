# Spec: <module_name>

Write a single Python module `<target_path>` for <one-line purpose>.

## Environment & constraints

- Python <version>, <allowed dependencies or "standard library only">.
- <Module-level constants with defaults, e.g. `DB_PATH = "data/kb.sqlite"`>.
- <Thread-safety / concurrency notes if relevant>.

## Function 1: `<name>(<params>) -> <return_type>`

- <One-line behaviour description>.
- <Edge cases, explicitly: empty input → `[]`; missing row → `None`; bad input → raise X>.

<Include exact algorithm steps when the behaviour is non-trivial>

## Function 2: `<name>(<params>) -> <return_type>`

- <as above>

## Output format

Output ONLY the module code in one code block. No tests in this output
(tests are generated separately from this same spec).