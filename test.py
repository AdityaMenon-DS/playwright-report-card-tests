"""Tests for the workshop report-card app.

Run with: python -m pytest test.py -v
Set APP_URL to switch between the main and test apps.
Set ROUNDS to repeat the tests with fresh sessions.
Requires pytest, pytest-playwright and pypdf.
"""
import os
import re

import pytest
from playwright.sync_api import Page, expect
from pypdf import PdfReader

APP_URL = os.environ.get('APP_URL', 'https://cs3002-26t3-workshop.onrender.com').rstrip('/')
ROUNDS = int(os.environ.get('ROUNDS', '1'))


@pytest.fixture(params=range(ROUNDS), ids=lambda n: f'round{n+1}')
def app(page: Page, request):
    page.set_default_timeout(15000)
    page.set_default_navigation_timeout(90000)
    page.goto(APP_URL + '/')
    expect(page.get_by_role('heading', name='Step 1: Your details')).to_be_visible()
    return page


def submit(page, name):
    # Wait for the form response before checking the page.
    with page.expect_navigation(wait_until='load'):
        page.get_by_role('button', name=name, exact=True).click()


def fill_details(page, email='student@example.com'):
    for label, value in [('Full name', 'Sample Student'),
                         ('Student ID', 'TEST001'),
                         ('Email address', email),
                         ('University', 'Example University')]:
        page.get_by_label(label).fill(value)


def to_academic(page):
    fill_details(page)
    submit(page, 'Continue')
    expect(page).to_have_url(APP_URL + '/academic')


def fill_academic(page):
    page.get_by_label('Major').select_option(label='Data Science')
    page.get_by_label('Academic year').fill('2026')
    page.get_by_label('Term').select_option(label='T3-2026')


def to_subjects(page):
    to_academic(page)
    fill_academic(page)
    submit(page, 'Continue')
    expect(page).to_have_url(APP_URL + '/subjects')


def add_subject(page, name, score):
    page.get_by_label('Subject name', exact=True).fill(name)
    page.get_by_label('Score', exact=True).fill(str(score))
    submit(page, 'Add subject')


def subject_rows(page):
    return page.locator('[data-testid^="subject-row-"]')


def test_valid_personal_details(app):
    to_academic(app)


def test_valid_academic_details(app):
    to_subjects(app)


def test_valid_subjects_review_and_pdf(app, tmp_path):
    to_subjects(app)
    add_subject(app, 'Mathematics', 80)
    add_subject(app, 'Physics', 60)
    expect(subject_rows(app)).to_have_count(2)
    submit(app, 'Review report')
    expect(app).to_have_url(APP_URL + '/review')
    preview = app.locator('[aria-label="Report card preview"]')
    for value in ['Sample Student', 'TEST001', 'Example University',
                  'Data Science', 'Mathematics', 'Physics', 'student@example.com']:
        expect(preview).to_contain_text(value)
    expect(app.get_by_test_id('text-overall-average')).to_have_text('70.0%')
    expect(app.get_by_test_id('text-overall-grade')).to_have_text('B')
    expect(app.get_by_test_id('review-subject-0')).to_have_text(re.compile(r'Mathematics\s*80\.0%\s*A'))
    expect(app.get_by_test_id('review-subject-1')).to_have_text(re.compile(r'Physics\s*60\.0%\s*C'))
    with app.expect_download() as download_info:
        app.get_by_role('link', name='Download report PDF').click()
    download = download_info.value
    assert download.failure() is None
    target = tmp_path / 'report.pdf'
    download.save_as(str(target))
    assert target.read_bytes().startswith(b'%PDF-'), 'Download must be a PDF'
    assert target.stat().st_size > 100, 'PDF must not be empty'


def test_remove_subject(app):
    to_subjects(app)
    add_subject(app, 'Mathematics', 80)
    add_subject(app, 'Physics', 60)
    submit(app, 'Remove Mathematics')
    expect(subject_rows(app)).to_have_count(1)
    expect(app.get_by_label('Subject 1 name', exact=True)).to_have_value('Physics')


@pytest.mark.parametrize('field', ['Full name', 'Student ID', 'Email address', 'University'])
def test_required_personal_field(app, field):
    fill_details(app)
    app.get_by_label(field).fill('')
    submit(app, 'Continue')
    expect(app).to_have_url(APP_URL + '/student')
    expect(app.get_by_role('heading', name='Step 1: Your details')).to_be_visible()


@pytest.mark.parametrize('email', ['not-an-email', 'student@', 'student.example.com'])
def test_invalid_email(app, email):
    fill_details(app, email)
    submit(app, 'Continue')
    expect(app).to_have_url(APP_URL + '/student')


@pytest.mark.parametrize('field', ['Major', 'Academic year', 'Term'])
def test_required_academic_field(app, field):
    to_academic(app)
    fill_academic(app)
    if field == 'Academic year':
        app.get_by_label(field).fill('')
    else:
        app.get_by_label(field).select_option(index=0)
    submit(app, 'Continue')
    expect(app).to_have_url(APP_URL + '/academic')


def test_no_subjects_rejected(app):
    to_subjects(app)
    submit(app, 'Review report')
    expect(app).to_have_url(APP_URL + '/subjects')
    expect(app.get_by_role('link', name='Download report PDF')).to_have_count(0)


@pytest.mark.parametrize('duplicate', ['Mathematics', 'mathematics', ' Mathematics '])
def test_duplicate_subject_rejected(app, duplicate):
    to_subjects(app)
    add_subject(app, 'Mathematics', 80)
    add_subject(app, duplicate, 60)
    expect(subject_rows(app)).to_have_count(1)
    expect(app.get_by_label('Subject 1 name', exact=True)).to_have_value('Mathematics')
    expect(app.get_by_label('Score for Mathematics', exact=True)).to_have_value('80.0')


@pytest.mark.parametrize('score', ['-1', '101', ''])
def test_invalid_score_rejected(app, score):
    to_subjects(app)
    add_subject(app, 'Mathematics', score)
    expect(subject_rows(app)).to_have_count(0)


def test_empty_subject_name_rejected(app):
    to_subjects(app)
    add_subject(app, '', 75)
    expect(subject_rows(app)).to_have_count(0)


@pytest.mark.parametrize('score,grade', [
    (0, 'U'), (39.9, 'U'), (40, 'E'), (49.9, 'E'),
    (50, 'D'), (59.9, 'D'), (60, 'C'), (69.9, 'C'),
    (70, 'B'), (79.9, 'B'), (80, 'A'), (89.9, 'A'),
    (90, 'S'), (100, 'S')])
def test_grade_boundaries(app, score, grade):
    to_subjects(app)
    add_subject(app, 'Boundary subject', score)
    expect(subject_rows(app)).to_have_count(1)
    expect(app.get_by_test_id('grade-subject-0')).to_have_text(grade)


def test_start_over_clears_details(app):
    to_subjects(app)
    add_subject(app, 'Mathematics', 80)
    app.once('dialog', lambda dialog: dialog.accept())
    submit(app, 'Start over')
    expect(app.get_by_role('heading', name='Step 1: Your details')).to_be_visible()
    for field in ['Full name', 'Student ID', 'Email address', 'University']:
        expect(app.get_by_label(field)).to_have_value('')


def test_pdf_contains_all_subjects(app, tmp_path):
    to_subjects(app)
    for name, score in [('Mathematics', 85), ('Physics', 65), ('Chemistry', 45)]:
        add_subject(app, name, score)
    submit(app, 'Review report')
    with app.expect_download() as result:
        app.get_by_role('link', name='Download report PDF').click()
    target = tmp_path / 'content-report.pdf'
    result.value.save_as(str(target))
    # Check the PDF contents too; a successful download alone is not enough.
    text = ' '.join(page.extract_text() or '' for page in PdfReader(target).pages)
    for name, score, grade in [('Mathematics', 85, 'A'), ('Physics', 65, 'C'), ('Chemistry', 45, 'E')]:
        assert re.search(rf'{name}\s+{score}%\s+{grade}\b', text), f'Missing or wrong PDF row: {name}'
    assert 'Overall average  65.0%' in text
    assert 'Overall grade: C' in text
