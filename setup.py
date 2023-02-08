import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="deprem_ocr",
    version="1.0.18",
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
    include_package_data=True,
    package_data={
        "deprem_ocr": [
            "deprem_ocr/ch_PP-OCRv3_rec_infer/*",
            "deprem_ocr/ch_PP-OCRv3_det_infer/*",
            "deprem_ocr/ppocr/ppocr_keys_v1.txt",
        ]
    },
    python_requires=">=3.10",
)
