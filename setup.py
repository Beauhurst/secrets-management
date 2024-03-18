import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="secrets-management",
    version="0.1.0",
    author="Beauhurst",
    author_email="noreply@beauhurst.com",
    description="Helper library for interacting with AWS Secrets Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/beauhurst/secrets-management",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "boto3",
        "django-environ",
    ],
)
