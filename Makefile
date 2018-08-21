
release-test:
	bumpversion patch
	python3 setup.py sdist bdist_wheel
	twine upload --repository pypitest dist/*

release:
	bumpversion patch
	python3 setup.py sdist bdist_wheel
	twine upload dist/*