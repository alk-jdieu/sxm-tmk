from setuptools import setup

setup(
    name="tmk",
    packages=["sxm_tmk"],
    entry_points={
        "console_scripts": [
            "tmk = sxm_tmk.cli.sxm_tmk:main",
        ]
    },
)
