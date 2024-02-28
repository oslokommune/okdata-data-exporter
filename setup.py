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
        "aws-xray-sdk>=2.12,<3",
        "boto3>=1.28.11",
        "okdata-aws>=2,<3",
        "okdata-resource-auth",
        "requests",
        # Not used directly, it's a transitive dependency from `aws-xray-sdk`,
        # but we need version 1.14 or above to make it work with Python 3.11.
        "wrapt>=1.14,<2",
    ],
)
