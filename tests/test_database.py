import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import DatabaseConnection


@pytest.fixture
def mock_mongo_client():
    """Fixture to provide a mocked MongoDB client"""
    with patch('app.MongoClient') as mock_client:
        yield mock_client


@pytest.fixture
def db_connection(mock_mongo_client):
    """Fixture to provide a DatabaseConnection instance with mocked MongoDB"""
    mock_instance = MagicMock()
    mock_db = MagicMock()
    mock_instance.admin.command.return_value = None
    mock_instance.__getitem__ = MagicMock(return_value=mock_db)
    mock_mongo_client.return_value = mock_instance
    
    with patch('app.MongoClient', return_value=mock_instance):
        conn = DatabaseConnection()
        conn.client = mock_instance
        conn.db = mock_db
        conn.connected = True
        yield conn


class TestDatabaseConnection:
    """Test suite for DatabaseConnection class"""
    
    def test_init(self, mock_mongo_client):
        """Test database initialization"""
        mock_instance = MagicMock()
        mock_instance.admin.command.return_value = None
        mock_mongo_client.return_value = mock_instance
        
        with patch('app.MongoClient', return_value=mock_instance):
            conn = DatabaseConnection()
            assert conn.client is not None
    
    def test_get_all_questions_empty(self, db_connection):
        """Test fetching questions when database is empty"""
        db_connection.db.questions.find.return_value.sort.return_value = []
        
        result = db_connection.get_all_questions()
        
        assert result == []
        db_connection.db.questions.find.assert_called_once()
    
    def test_get_all_questions_with_data(self, db_connection):
        """Test fetching questions with sample data"""
        sample_questions = [
            {
                '_id': '12345',
                'question': 'What is 2+2?',
                'options': ['3', '4', '5'],
                'correct': 1,
                'explanation': 'Because 2+2=4'
            },
            {
                '_id': '12346',
                'question': 'Capital of France?',
                'options': ['London', 'Paris', 'Berlin'],
                'correct': 1,
                'explanation': 'Paris is the capital'
            }
        ]
        
        db_connection.db.questions.find.return_value.sort.return_value = sample_questions
        
        result = db_connection.get_all_questions()
        
        assert len(result) == 2
        assert result[0]['question'] == 'What is 2+2?'
        assert result[1]['question'] == 'Capital of France?'
    
    def test_add_question_success(self, db_connection):
        """Test adding a question successfully"""
        result = db_connection.add_question(
            question_text='Test Question?',
            options=['Option A', 'Option B', 'Option C'],
            correct_index=0,
            explanation='Test explanation'
        )
        
        assert result is True
        db_connection.db.questions.insert_one.assert_called_once()
        
        # Verify the inserted document structure
        call_args = db_connection.db.questions.insert_one.call_args[0][0]
        assert call_args['question'] == 'Test Question?'
        assert call_args['options'] == ['Option A', 'Option B', 'Option C']
        assert call_args['correct'] == 0
        assert call_args['explanation'] == 'Test explanation'
    
    def test_add_question_no_connection(self, mock_mongo_client):
        """Test adding a question when database is not connected"""
        mock_instance = MagicMock()
        mock_instance.admin.command.side_effect = Exception("Connection failed")
        mock_mongo_client.return_value = mock_instance
        
        with patch('app.MongoClient', return_value=mock_instance):
            conn = DatabaseConnection()
            conn.connected = False
            conn.db = None
            
            result = conn.add_question(
                question_text='Test Question?',
                options=['A', 'B'],
                correct_index=0
            )
            
            assert result is False
    
    def test_delete_question_success(self, db_connection):
        """Test deleting a question successfully"""
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        db_connection.db.questions.delete_one.return_value = mock_result
        
        result = db_connection.delete_question('507f1f77bcf86cd799439011')
        
        assert result is True
        db_connection.db.questions.delete_one.assert_called_once()
    
    def test_delete_question_not_found(self, db_connection):
        """Test deleting a question that doesn't exist"""
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        db_connection.db.questions.delete_one.return_value = mock_result
        
        result = db_connection.delete_question('nonexistent_id')
        
        assert result is False
    
    def test_update_question_success(self, db_connection):
        """Test updating a question successfully"""
        mock_result = MagicMock()
        mock_result.modified_count = 1
        db_connection.db.questions.update_one.return_value = mock_result
        
        result = db_connection.update_question(
            question_id='507f1f77bcf86cd799439011',
            question_text='Updated Question?',
            options=['New A', 'New B'],
            correct_index=1,
            explanation='Updated explanation'
        )
        
        assert result is True
        db_connection.db.questions.update_one.assert_called_once()
    
    def test_delete_all_questions_success(self, db_connection):
        """Test deleting all questions successfully"""
        mock_result = MagicMock()
        mock_result.deleted_count = 5
        db_connection.db.questions.delete_many.return_value = mock_result
        
        result = db_connection.delete_all_questions()
        
        assert result is True
        db_connection.db.questions.delete_many.assert_called_once_with({})
    
    def test_close_connection(self, db_connection):
        """Test closing the database connection"""
        db_connection.close()
        
        db_connection.client.close.assert_called_once()
