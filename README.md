<!-- These are examples of badges you might want to add to your README:
     please update the URLs accordingly

[![Built Status](https://api.cirrus-ci.com/github/<USER>/progressive-automations-python.svg?branch=main)](https://cirrus-ci.com/github/<USER>/progressive-automations-python)
[![ReadTheDocs](https://readthedocs.org/projects/progressive-automations-python/badge/?version=latest)](https://progressive-automations-python.readthedocs.io/en/stable/)
[![Coveralls](https://img.shields.io/coveralls/github/<USER>/progressive-automations-python/main.svg)](https://coveralls.io/r/<USER>/progressive-automations-python)
[![PyPI-Server](https://img.shields.io/pypi/v/progressive-automations-python.svg)](https://pypi.org/project/progressive-automations-python/)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/progressive-automations-python.svg)](https://anaconda.org/conda-forge/progressive-automations-python)
[![Monthly Downloads](https://pepy.tech/badge/progressive-automations-python/month)](https://pepy.tech/project/progressive-automations-python)
[![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter)](https://twitter.com/progressive-automations-python)
-->

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# progressive-automations-python

> Python package for programmatically controlling Progressive Automations desk lifters (e.g., LG-07 modular lifting column via FLTCON) with Prefect workflow orchestration.

Control your desk lifter remotely via Prefect Cloud deployments with asynchronous execution and position polling. Perfect for laboratory automation where the desk position needs to be coordinated with other equipment.

## Quick Start

```bash
# 1. Install
pip install progressive-automations-python

# 2. Configure Prefect Cloud
prefect cloud login -k <your-api-key>
prefect work-pool create desk-lifter-pool --type process

# 3. Deploy flows
python -c "from progressive_automations_python.deployment import create_deployments; create_deployments()"

# 4. Start worker on Raspberry Pi
prefect worker start --pool desk-lifter-pool
```

## Usage

Trigger movements asynchronously from any Python environment:

```python
from prefect.deployments import run_deployment

# Trigger movement (returns immediately)
flow_run = run_deployment(
    name="simple-movement-flow/move-to-position",
    parameters={"target_height": 35.5},
    timeout=0  # Don't wait, return immediately
)

# Poll status later
# ... (see documentation for polling examples)
```

## Documentation

- [Installation and Usage Guide](docs/installation-and-usage.md) - Complete setup and API reference
- [Raspberry Pi Setup](docs/raspberry-pi-setup.md) - Hardware configuration
- [Bill of Materials](docs/bill_of_materials.md) - Required components


<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.6. For details and usage
information on PyScaffold see https://pyscaffold.org/.
