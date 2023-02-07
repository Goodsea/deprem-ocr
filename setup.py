import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="deprem_ocr",
    version="1.0.9",
    author="Kutsal Ozkurt",
    author_email="kutsal_baran@hotmail.com",
    description="Extract texts from images and screenshots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Goodsea/deprem-ocr",
    project_urls={
        "Bug Tracker": "https://github.com/Goodsea/deprem-ocr/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
)
