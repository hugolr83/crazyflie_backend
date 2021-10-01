# Backend

Code pour le Backend du cours d'INF3995

## Requis

* Python 3.9
* Poetry ([installation](https://python-poetry.org/docs/))

## Rouler l'API en local

Commandes:
```bash
poetry install
poetry shell
sh setup-env.sh
python backend/app.py
```

Ou simplement utiliser PyCharm avec le plugin de Poetry

## Build l'image Docker

Commandes:
```bash
docker build . -t registry.gitlab.com/polytechnique-montr-al/inf3995/20213/equipe-100/inf3995-backend/backend:<version>
docker push registry.gitlab.com/polytechnique-montr-al/inf3995/20213/equipe-100/inf3995-backend/backend:<version>
```
