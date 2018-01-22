from setuptools import setup, find_packages

requirements = open("requirements.txt").readlines()
extra_requirements = {
    'scripts': open("extra-requirements-scripts.txt").readlines()
}
version = open("version.txt").readline()

setup(
    name='releasewarrior',
    version=version,
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require=extra_requirements,
    entry_points="""
        [console_scripts]
        release=releasewarrior.cli:cli
    """,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
