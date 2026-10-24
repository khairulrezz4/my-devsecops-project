# Python pipeline POC

This small application validates the reusable CI pipeline's Python build,
test, configuration-validation, security-scan, and artifact-upload paths.

Run locally:

```text
python build.py
python -m unittest discover -s . -p "test_*.py"
```
