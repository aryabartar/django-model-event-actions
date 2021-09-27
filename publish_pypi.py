import os

os.system("python setup.py bdist_wheel sdist")
os.system("twine upload dist/*")
