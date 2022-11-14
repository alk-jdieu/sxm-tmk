# Supplier XM - Environment management

`sxm-tmk` is a tool that facilitates environment management across platforms by leveraging conda in order to:

- avoid recompiling your dependencies
- manage cross platform environment
- capture non-python dependencies to achieve reproductibility

# Features

Allow you to:

- create an environment from pipenv to conda

# Usage

Say you have an environment managed with `pipenv` or `poetry`. To convert it to conda:

`tmk convert /Users/js-dieu/Projects/service-test`

The system will automatically discover if you are using `pipenv` or `poetry` and then fetch your environment specification
in order to convert it to conda.
