import os
from setuptools import setup, find_packages # type: ignore

# Read the contents of README file
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Development dependencies
dev_requires = [
    'pytest>=7.0.0',
    'pytest-cov>=4.0.0',
    'coverage>=7.0.0',
    'black>=22.0.0',
    'isort>=5.0.0',
    'flake8>=4.0.0',
    'mypy>=0.900',
    'twine>=4.0.0',
]

setup(
    name="py-troya-connect",
    version="0.1.3152",
    packages=find_packages(exclude=['tests*', 'docs*']),
    
    # Dependencies
    install_requires=[
        "pywin32>=223",
        "typing-extensions>=4.0.0; python_version < '3.8'",
    ],
    extras_require={
        'dev': dev_requires,
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
    
    # Metadata
    author="Tolga Kurtulus",
    author_email="tolgakurtulus95@gmail.com",
    description="A Python interface for Attachmate Extra! X-treme",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="terminal, attachmate, extra, automation, thy, turkish airlines",
    
    # URLs
    url="https://github.com/tolgakurtuluss/py-troya-connect",
    project_urls={
        "Bug Tracker": "https://github.com/tolgakurtuluss/py-troya-connect/issues",
        "Documentation": "https://github.com/tolgakurtuluss/py-troya-connect/wiki",
        "Source Code": "https://github.com/tolgakurtuluss/py-troya-connect",
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: System :: Networking",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    
    # Package config
    python_requires=">=3.8",
    zip_safe=False,
    include_package_data=True,
    
    # Entry points
    entry_points={
        'console_scripts': [
            'py-troya=py_troya_connect.terminal:main',
        ],
    },
)
