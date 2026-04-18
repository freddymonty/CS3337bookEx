# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 6.0.1 book-exchange coursework app (CSULA CS 3337). Single project `bookEx` with one app `bookMng`. SQLite (`db.sqlite3`) is checked in and used as the dev database. Dependencies are pinned in `requirements.txt` (just Django right now) — install into the active Python env with `pip install -r requirements.txt` or `conda install -c conda-forge django=6.0.1`. Django 6.0 requires Python ≥ 3.12; Anaconda's `base` env on a fresh install typically satisfies this.

## Commands

Run from the repo root (where `manage.py` lives). From PyCharm, create a Python run config pointing at `manage.py` with parameters `runserver 127.0.0.1:8000`. From a shell (Anaconda Prompt — plain PowerShell often resolves `python` to a non-conda interpreter without Django):

- `python manage.py runserver` — start dev server at http://127.0.0.1:8000/
- `python manage.py makemigrations bookMng` — after editing `bookMng/models.py`
- `python manage.py migrate` — apply migrations
- `python manage.py createsuperuser` — needed to access `/admin/` and seed `MainMenu` entries (the sidebar is data-driven; a fresh DB shows an empty sidebar until menu rows exist)
- `python manage.py test bookMng` — run app tests (`bookMng/tests.py` is currently a stub)
- `python manage.py test bookMng.tests.ClassName.test_method` — run a single test

## Architecture

**Two-layer URL routing.** `bookEx/urls.py` mounts `bookMng.urls` at `/` and also includes `django.contrib.auth.urls` for login/logout/password flows. Registration is a custom `CreateView` (`bookMng.views.Register`) wired at the project level, not inside the app — keep new auth-adjacent routes consistent with that split.

**Templates are centralized, not per-app.** `TEMPLATES.DIRS = [BASE_DIR/'bookEx/templates']` in `bookEx/settings.py`. App templates live at `bookEx/templates/bookMng/*.html` and auth templates at `bookEx/templates/registration/*.html`. `APP_DIRS` is also True, but nothing currently uses `bookMng/templates/` — follow the centralized convention.

**Every page extends `base.html` and populates two blocks: `sidenav` and `content`.** The sidebar is rendered from `MainMenu.objects.all()`, so every view that renders a page must pass `item_list` in its context (see existing views for the pattern). Missing it produces an empty sidebar, not an error.

**Static files and uploads share a directory.** `STATICFILES_DIRS = [BASE_DIR/'bookEx/static']` and `Book.picture` has `upload_to='bookEx/static/uploads'`. Views compute `book.pic_path = book.picture.url[14:]` (strips the leading `"/bookEx/static"` prefix) so templates can render via `{% static book.pic_path %}`. This slice is brittle: if you move the upload path or change `STATIC_URL`, update the slice everywhere it appears (`displaybooks`, `book_detail`, `mybooks`). There is no `MEDIA_URL`/`MEDIA_ROOT` configured — uploads work only because they land inside the static dir during dev.

**Rating model maintains a denormalized average on `Book`.** `Rating.save()` and `Rating.delete()` both call `book.update_average_rating()`, which recomputes `Book.average_rating` via `aggregate(Avg('rating'))`. `Meta.unique_together = ('book', 'user')` enforces one rating per user per book. When adding new rating mutation paths (e.g. bulk update, admin action), make sure the average stays in sync — don't bypass these hooks with `.update()` or `bulk_create`.

**Ownership rules differ per feature.** `rate_book` blocks users from rating their own posted books (view-level redirect + template-level button hide). `add_comment` deliberately does *not* have this restriction — authors are allowed to comment on their own books. When adding new interaction features, decide explicitly per feature; don't default to the rating rule.

**Comment flow.** `Comment` model has FK to `Book` (via `related_name='comments'`) and `User`, a `TextField`, and `created_at` with `Meta.ordering = ['-created_at']` (newest first). Reading is public (rendered inline on `book_detail.html` below the book info table); posting goes through `add_comment` (`@login_required`, POST-only, redirects back to `book_detail`). The `book_detail` view itself is a pure GET — it passes `comments` and `form` to the template, with `form=None` for anonymous users so the template can show a "log in to comment" message instead.

## Branches / workflow

This is a coursework repo; `master` is the submission branch. Feature work happens on `feature/<name>` branches — e.g. `feature/comment-section` — merged to master via PR once verified locally. Don't commit `db.sqlite3` churn from `createsuperuser` runs or PyCharm's `.idea/bookEx.iml` interpreter edits unless intentionally changing those.
