"""baseline (schema existant via create_all - point de depart des migrations)

Revision vide intentionnellement : le schema actuel (prod MySQL comme dev SQLite)
a ete cree via Base.metadata.create_all() (voir database.py:init_db), pas via Alembic.
Pour ne PAS tenter de recreer/dropper des tables existantes, cette revision ne fait rien.

Usage :
  - Sur une base existante (prod actuelle) : `alembic stamp head` (marque cette revision
    comme appliquee sans rien executer).
  - Sur une base neuve : `alembic upgrade head` (ne fait rien, puis create_all() au
    demarrage de l'app cree les tables — a terme, migrer create_all() vers de vraies
    migrations Alembic pour chaque nouveau changement de modele).
  - A partir de maintenant : toute modification de models.py doit passer par
    `alembic revision --autogenerate -m "..."` puis relecture manuelle du diff genere.

Revision ID: d1f37630ccad
Revises: 
Create Date: 2026-08-05 21:44:07.027657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f37630ccad'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
