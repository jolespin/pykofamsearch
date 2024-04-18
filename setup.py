from setuptools import setup

# Version
# version = None
# with open("./pykofamsearch/__init__.py", "r") as f:
#     for line in f.readlines():
#         line = line.strip()
#         if line.startswith("__version__"):
#             version = line.split("=")[-1].strip().strip('"')
# assert version is not None, "Check version in pykofamsearch/__init__.py"

exec(open('pykofamsearch/__init__.py').read())

setup(name='pykofamsearch',
      version=__version__,
      description='Kofam prediction using PyHmmer',
      url='https://github.com/new-atlantis-labs/pykofamsearch',
      author='Josh L. Espinoza',
      author_email='jolespin@newatlantis.io, jol.espinoz@gmail.com',
      license='MIT License',
      packages=["pykofamsearch"],
      install_requires=[
      "pyhmmer >=0.10.11",
      "pandas",
      "tqdm",
      ],
    include_package_data=False,
     scripts=[
         "pykofamsearch/pykofamsearch.py",
         "pykofamsearch/reformat_pykofamsearch.py",
         ],

)

