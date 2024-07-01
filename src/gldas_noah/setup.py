from setuptools import find_packages, setup

setup(
    name="gldas_noah",
    packages=find_packages(exclude=["gldas_noah_tests"]),
    install_requires=[
        "dagster==1.7.12",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
