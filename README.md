# Campus Lost-and-Found System

Students, teachers, staff, and security workers often lose or find personal items on campus. Information is currently spread across messaging groups, social media, and security desks. The Campus Lost-and-Found System provides one place to report, search for, match, claim, and safely return items.

Built by Solid Squad.

## Architecture

The backend is a Django modular monolith. Planned apps:

| App | Responsibility |
| --- | --- |
| accounts | University SSO authentication |
| items | Lost and found item management |
| matching | Automated matching of reported items |
| claims | Ownership verification and handover |
| notifications | Email and push notifications |

PostgreSQL is the planned data store. Users authenticate through University SSO.

The repository currently contains the Django project scaffold and architecture documents. The apps above are not implemented yet.

- [Architecture](docs/architecture.md)
- [ADR-001: Django modular monolith](docs/adr_001.md)

## Project layout

lost-and-found/
├── README.md
├── docs/ # architecture notes and decisions
└── src/ # Django project
├── manage.py
└── lostandfound/ # project settings, URLs, ASGI, and WSGI

## Local setup

Requires Python 3.12 or newer. The project was generated with Django 6.1.

python3 -m venv .venv
source .venv/bin/activate
pip install "django==6.1.2"
python src/manage.py runserver

The development server runs at http://127.0.0.1:8000/
