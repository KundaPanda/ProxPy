import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as req:
    requirements = req.read().splitlines()

setuptools.setup(
    name="ProxPy",
    version="0.0.2",
    author="KundaPanda",
    author_email="vojdoh@gmail.com",
    description="Python multithreading-ready proxy wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KundaPanda/ProxPy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
)
