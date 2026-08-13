# BookFlow LMS

> A polished Arabic RTL dashboard for library inventory, book lending, and catalogue management.

BookFlow LMS is a Django application that gives small libraries a clear operational view of their books. It combines inventory statistics, searchable catalogue management, category organization, media uploads, and safe edit/delete workflows in a focused interface.

## Product overview

The project is designed around the daily workflow of a library manager rather than a generic e-commerce store. The dashboard shows the current inventory split between available, rented, and sold books, while the catalogue supports title/author search and filtering by status or category.

| Capability | Included |
| --- | --- |
| Arabic RTL interface | Yes |
| Inventory dashboard | Yes |
| Book creation and editing | Yes |
| Book cover and author image uploads | Yes |
| Category management | Yes |
| Search by title or author | Yes |
| Filter by status and category | Yes |
| Sales and rental revenue totals | Yes |
| Django admin | Yes |
| Responsive mobile layout | Yes |

## Technology

- **Backend:** Python, Django 5.2
- **Database:** SQLite for local/demo use; PostgreSQL through `DATABASE_URL` in production
- **Frontend:** Django Templates, semantic HTML, custom CSS, lightweight JavaScript
- **Static files:** WhiteNoise with Django `collectstatic`
- **Deployment:** Vercel-compatible WSGI deployment

## Run locally

The project requires Python 3.10 or newer. The following commands create an isolated environment, install dependencies, initialize the database, and start the development server.

```bash
git clone https://github.com/MahmoudAlmodalal/bookflow-lms.git
cd bookflow-lms
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser. To use the Django admin, create a local administrator with `python manage.py createsuperuser` and visit `/admin/`.

## Configuration

Production environments should provide a long random `SECRET_KEY`, set `DEBUG=0`, define `ALLOWED_HOSTS`, and use a managed PostgreSQL database through `DATABASE_URL`. The repository includes `.env.example` as a safe starting point; secrets should never be committed.

```ini
DEBUG=0
SECRET_KEY=replace-with-a-long-random-secret
ALLOWED_HOSTS=your-domain.com,.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-domain.com
DATABASE_URL=postgresql://user:password@host:5432/bookflow
```

## Deploy to Vercel

Vercel detects the Django project from `manage.py` and the WSGI entry point in `lms/wsgi.py`. Connect this repository to a Vercel project, configure the environment variables above, and deploy the `main` branch. The included `vercel.json` sets the WSGI function duration and the build automatically collects static assets.

> SQLite is suitable for a portfolio/demo deployment. For persistent writes in a real production environment, use PostgreSQL and external object storage for uploaded media.

## Project structure

```text
.
├── lms/                    # Django project settings, URLs, WSGI and static vendor assets
├── lms_app/                # Library models, forms, views, tests and custom assets
├── templates/              # Arabic RTL dashboard and catalogue templates
├── media/                  # Local development media directory
├── db.sqlite3              # Included demo dataset for local exploration
├── manage.py
├── requirements.txt
├── vercel.json
└── .env.example
```

## Quality checks

Run Django's system checks and test suite before pushing changes:

```bash
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

## License

This project is released under the MIT License. See `LICENSE` if a license file is added to the repository.
