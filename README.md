# README

## installation and development

```bash
#Install package given a conda environment with python>3.9
git clone https://github.com/DeanLight/graph_rewrite
cd graph_rewrite
pip install -e .

```

For docker development/usage
```bash
cd graph_rewrite
# build container
docker-compose build

# spin up the container
docker-compose up

# get a bash terminal on a spun up container
docker-compose exec main bash

# spin up and get a bash terminal (closing it will close the container)
docker-compose run main bash

```