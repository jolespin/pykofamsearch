from setuptools import setup

# Version
exec(open('pykofamsearch/__init__.py').read())

setup(name='pykofamsearch',
      version=__version__,
      description='Fast implementation of KofamScan optimized for high-memory systems using PyHmmer',
      url='https://github.com/jolespin/pykofamsearch',
      author='Josh L. Espinoza',
      author_email='jolespin@newatlantis.io, jol.espinoz@gmail.com',
      license='MIT License',
      packages=["pykofamsearch"],
      install_requires=[
      "pyhmmer >=0.10.12",
      "pandas",
      "tqdm",
      ],
    include_package_data=False,
    entry_points={
        'console_scripts': [
            'pykofamsearch=pykofamsearch.pykofamsearch:main',   # Executes pykofamsearch.main()
            'reformat_enzymes=pykofamsearch.reformat_enzymes:main',  # Executes reformat_enzymes.main()
            'reformat_pykofamsearch=pykofamsearch.reformat_pykofamsearch:main',  # Executes reformat_pykofamsearch.main()
            'serialize_kofam_models=pykofamsearch.serialize_kofam_models:main',  # Executes serialize_kofam_models.main()
            'subset_serialized_models=pykofamsearch.subset_serialized_models:main',  # Executes subset_serialized_models.main()
        ],
    },
    #  scripts=[
    #      "pykofamsearch/pykofamsearch.py",
    #      "pykofamsearch/reformat_pykofamsearch.py",
    #      "pykofamsearch/serialize_kofam_models.py",
    #      "pykofamsearch/subset_serialized_models.py",
    #      ],
)

