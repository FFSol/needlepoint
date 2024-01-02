import unittest
from app import app, db
from app.models import User

class TestModels(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for testing
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        user = User(username='testuser', email='test@example.com', password='testpassword')
        db.session.add(user)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)

if __name__ == '__main__':
    unittest.main()
