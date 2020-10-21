import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ThumbnailFlow", # Replace with your own username
    version="0.1.0",
    author="Jens Hinghaus",
    author_email="jhinghaus@gmail.com",
    description="Generator for thumbnails",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=None, #TODO GitHub-Link
    keywords="thumbnails",
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        "Development Status :: 3 - Alpha"
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Topic :: Multimedia :: Graphics",
    ],
    install_requires=['Pillow'],
    python_requires='>=3.6',
)
