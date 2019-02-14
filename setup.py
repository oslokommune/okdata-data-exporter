import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="data-exporter",
    version="0.0.1",
    author="Origo Dataplattform",
    author_email="dataplattform@oslo.kommune.no",
    description="TODO",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.oslo.kommune.no/origo-dataplatform/data-exporter",
    packages=setuptools.find_packages(),
    install_requires=[
        'docutils==0.14',
        'jmespath==0.9.3',
        'python-dateutil==2.7.5',
        's3transfer==0.1.13',
        'six==1.12.0',
        'urllib3==1.24.1',
        'pytest==4.2.1'
    ]
)