# Backend

Code pour le Backend du cours d'INF3995

## Requis

* Python 3.9
* Poetry ([installation](https://python-poetry.org/docs/))

## Rouler l'API en local

Commandes (dans le root):
```bash
poetry install
poetry shell
python backend/app.py
```

Ou simplement utiliser PyCharm avec le plugin de Poetry

## Rouler les tests

Commandes (dans le root):
```bash
poetry run pytest
```

## Build l'image Docker

Commandes:
```bash
docker build . -t registry.gitlab.com/polytechnique-montr-al/inf3995/20213/equipe-100/inf3995-backend/backend:<version>
docker push registry.gitlab.com/polytechnique-montr-al/inf3995/20213/equipe-100/inf3995-backend/backend:<version>
```

## Rouler l'image en local
```bash
docker run -p 8000:8000 registry.gitlab.com/polytechnique-montr-al/inf3995/20213/equipe-100/inf3995-backend/backend:<version>
```
Naviger ensuite à [http://localhost:8000/docs](http://localhost:8000/docs) (et non 0.0.0.0) et choisir l'endpoint dev dans la liste
