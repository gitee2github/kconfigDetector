#!/usr/bin/env python3
"""
Description: setup up the kconfigDetector.
"""

from setuptools import setup, find_packages


setup(
    name='kconfigDetector',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'ply'
        ],
    python_requires='>=3',
    url='https://gitee.com/openeuler/kconfigDetector',
    author='sunying',
    author_email='sunying@nj.iscas.ac.cn',
    # 生成可执行文件
    entry_points={
        'console_scripts':[
            'check_kconfig_dep = kconfigDepDetector.check_kconfig_dep:main'
        ]
    },
    zip_safe=False
)
