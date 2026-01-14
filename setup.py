from grafana_backup.constants import (PKG_NAME, PKG_VERSION)
from setuptools import setup, find_packages

# Global variables
name = PKG_NAME
version = PKG_VERSION
requires = [
    'requests>=2.32,<3.0',
    'docopt>=0.6,<1.0',
    'boto3>=1.42,<2.0',
    'azure-storage-blob>=12.28,<13.0',
    'google-cloud-storage>=3.8,<4.0',
    'influxdb>=5.3,<6.0',
    'packaging>=25.0,<26.0'
]

setup(
    name=name,
    version=version,
    description='A Python-based application to backup Grafana settings using the Grafana API',
    long_description_content_type='text/markdown',
    long_description=open('README.md', 'r').read(),
    author="author",
    author_email="ysde108@gmail.com",
    url="https://github.com/ysde/grafana-backup-tool",
    entry_points={
        'console_scripts': [
            'grafana-backup = grafana_backup.cli:main'
        ]
    },
    packages=find_packages(),
    install_requires=requires,
    package_data={'': ['conf/*']},
)
