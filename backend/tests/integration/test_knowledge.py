import pytest
from backend.app.models import KnowledgeArticle, Incident, Application, User, AuditLog
from backend.extensions import db
from backend.tests.conftest import auth_headers


def test_create_article_as_support(client, support_user_id):
    support = db.session.get(User, support_user_id)
    response = client.post(
        '/api/knowledge',
        json={
            'title': 'Test Article',
            'content': 'This is test content.',
            'tags': 'test,example'
        },
        headers=auth_headers(support)
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Test Article'
    assert data['author_id'] == support.id
    assert data['tags'] == 'test,example'


def test_create_article_as_reporter_denied(client, reporter_user_id):
    reporter = db.session.get(User, reporter_user_id)
    response = client.post(
        '/api/knowledge',
        json={'title': 'Reporter Article', 'content': 'Should fail'},
        headers=auth_headers(reporter)
    )
    assert response.status_code == 403


def test_search_articles_by_title(client, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    a1 = KnowledgeArticle(title='Python troubleshooting', content='...', tags='python', author_id=admin.id)
    a2 = KnowledgeArticle(title='Database connection issue', content='...', tags='db', author_id=admin.id)
    db.session.add_all([a1, a2])
    db.session.commit()

    response = client.get('/api/knowledge/search?q=python', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Python troubleshooting'


def test_search_articles_by_tag(client, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    a1 = KnowledgeArticle(title='Article with tag', content='...', tags='sql,performance', author_id=admin.id)
    a2 = KnowledgeArticle(title='Another article', content='...', tags='python', author_id=admin.id)
    db.session.add_all([a1, a2])
    db.session.commit()

    response = client.get('/api/knowledge/search?q=performance', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Article with tag'


def test_link_article_to_incident(client, support_user_id, reporter_user_id):
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
    db.session.add(app)
    db.session.commit()
    incident = Incident(title='Test Incident', description='test', application_id=app.id, reporter_id=reporter.id, status='new')
    db.session.add(incident)
    db.session.commit()
    article = KnowledgeArticle(title='How to fix', content='Steps', author_id=support.id)
    db.session.add(article)
    db.session.commit()

    # Link
    response = client.post(
        f'/api/knowledge/{article.id}/incidents/{incident.id}',
        headers=auth_headers(support)
    )
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Article linked'

    # Check incident response includes knowledge_articles
    response = client.get(f'/api/incidents/{incident.id}', headers=auth_headers(support))
    assert response.status_code == 200
    data = response.get_json()
    assert 'knowledge_articles' in data
    assert len(data['knowledge_articles']) == 1
    assert data['knowledge_articles'][0]['id'] == article.id
    assert data['knowledge_articles'][0]['title'] == 'How to fix'

    # Check audit log
    audit = AuditLog.query.filter_by(incident_id=incident.id, field_changed='knowledge_linked').first()
    assert audit is not None
    assert 'How to fix' in audit.new_value


def test_unlink_article(client, support_user_id, reporter_user_id):
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app = Application(name='Test App 2', description='test', criticality='medium', owner_id=reporter.id)
    db.session.add(app)
    db.session.commit()
    incident = Incident(title='Test Incident 2', description='test', application_id=app.id, reporter_id=reporter.id, status='new')
    db.session.add(incident)
    db.session.commit()
    article = KnowledgeArticle(title='To unlink', content='...', author_id=support.id)
    db.session.add(article)
    db.session.commit()

    # Link first
    client.post(f'/api/knowledge/{article.id}/incidents/{incident.id}', headers=auth_headers(support))

    # Unlink
    response = client.delete(
        f'/api/knowledge/{article.id}/incidents/{incident.id}',
        headers=auth_headers(support)
    )
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Article unlinked'

    # Check incident response now has no articles
    response = client.get(f'/api/incidents/{incident.id}', headers=auth_headers(support))
    data = response.get_json()
    assert len(data['knowledge_articles']) == 0

    # Check audit log for unlink
    audit = AuditLog.query.filter_by(incident_id=incident.id, field_changed='knowledge_unlinked').first()
    assert audit is not None
    assert 'To unlink' in audit.old_value
def test_update_article_as_support(client, support_user_id):
    support = db.session.get(User, support_user_id)
    # Create article
    response = client.post(
        '/api/knowledge',
        json={'title': 'Original', 'content': 'Original content', 'tags': 'test'},
        headers=auth_headers(support)
    )
    assert response.status_code == 201
    article = response.get_json()

    # Update
    update_response = client.put(
        f'/api/knowledge/{article["id"]}',
        json={'title': 'Updated Title', 'content': 'New content', 'tags': 'updated'},
        headers=auth_headers(support)
    )
    assert update_response.status_code == 200
    data = update_response.get_json()
    assert data['title'] == 'Updated Title'
    assert data['content'] == 'New content'
    assert data['tags'] == 'updated'


def test_update_article_as_reporter_denied(client, reporter_user_id, support_user_id):
    support = db.session.get(User, support_user_id)
    # Create article as support
    response = client.post(
        '/api/knowledge',
        json={'title': 'To Update', 'content': 'content', 'tags': ''},
        headers=auth_headers(support)
    )
    assert response.status_code == 201
    article = response.get_json()

    # Try update as reporter
    reporter = db.session.get(User, reporter_user_id)
    update_response = client.put(
        f'/api/knowledge/{article["id"]}',
        json={'title': 'Hacked'},
        headers=auth_headers(reporter)
    )
    assert update_response.status_code == 403


def test_update_article_not_found(client, support_user_id):
    support = db.session.get(User, support_user_id)
    response = client.put(
        '/api/knowledge/99999',
        json={'title': 'Not Found'},
        headers=auth_headers(support)
    )
    assert response.status_code == 404


def test_delete_article_as_support(client, support_user_id):
    support = db.session.get(User, support_user_id)
    # Create article
    response = client.post(
        '/api/knowledge',
        json={'title': 'To Delete', 'content': 'content', 'tags': ''},
        headers=auth_headers(support)
    )
    assert response.status_code == 201
    article = response.get_json()

    # Delete
    delete_response = client.delete(
        f'/api/knowledge/{article["id"]}',
        headers=auth_headers(support)
    )
    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == 'Article deleted'

    # Verify gone
    get_response = client.get(f'/api/knowledge/{article["id"]}', headers=auth_headers(support))
    assert get_response.status_code == 404


def test_delete_article_as_reporter_denied(client, reporter_user_id, support_user_id):
    support = db.session.get(User, support_user_id)
    response = client.post(
        '/api/knowledge',
        json={'title': 'To Delete Denied', 'content': 'content'},
        headers=auth_headers(support)
    )
    assert response.status_code == 201
    article = response.get_json()

    reporter = db.session.get(User, reporter_user_id)
    delete_response = client.delete(
        f'/api/knowledge/{article["id"]}',
        headers=auth_headers(reporter)
    )
    assert delete_response.status_code == 403