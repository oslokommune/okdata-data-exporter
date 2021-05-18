import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="okdata-data-exporter",
    version="0.0.1",
    author="Origo Dataplattform",
    author_email="dataplattform@oslo.kommune.no",
    description="Lambda function to export data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oslokommune/okdata-data-exporter",
    packages=setuptools.find_packages(),
    install_requires=[
        "aws-xray-sdk",
        "boto3",
        "okdata-aws",
        "okdata-resource-auth",
        "requests",
    ],
)
