
release-test:
	bumpversion patch
	rm -rf dist
	python3 setup.py bdist_wheel
	twine upload --repository pypitest dist/*

release:
	bumpversion patch
	rm -rf dist
	python3 setup.py sdist bdist_wheel
	twine upload dist/*