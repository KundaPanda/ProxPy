python setup.py sdist bdist_wheel && python -m twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*
