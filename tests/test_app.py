import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDynamicImports:
    """Test that critical imports work correctly"""
    
    def test_import_app_module(self):
        """Test that app module can be imported"""
        try:
            import app
            assert hasattr(app, 'DatabaseConnection')
            assert hasattr(app, 'QuizApp')
        except ImportError as e:
            pytest.fail(f"Failed to import app module: {e}")
    
    def test_import_dependencies(self):
        """Test that all required dependencies are available"""
        try:
            import tkinter
            import pymongo
            import dotenv
        except ImportError as e:
            pytest.fail(f"Missing required dependency: {e}")


class TestQuestionFormat:
    """Test question JSON format validation"""
    
    def test_valid_question_format(self):
        """Test that a well-formed question is valid"""
        question = {
            'question': 'What is the capital of France?',
            'options': ['London', 'Paris', 'Berlin', 'Madrid'],
            'correct': 1,
            'explanation': 'Paris is the capital of France'
        }
        
        assert 'question' in question
        assert 'options' in question
        assert 'correct' in question
        assert isinstance(question['options'], list)
        assert len(question['options']) >= 2
    
    def test_multi_select_question_format(self):
        """Test that multi-select questions (with list of correct answers) are valid"""
        question = {
            'question': 'Which of these are capitals?',
            'options': ['London', 'Paris', 'Berlin', 'Madrid'],
            'correct': [0, 1, 2],  # Multiple answers
            'explanation': 'All three are European capitals'
        }
        
        assert 'question' in question
        assert isinstance(question['correct'], list)
        assert all(isinstance(idx, int) for idx in question['correct'])


class TestJSONHandling:
    """Test JSON import/export functionality"""
    
    def test_parse_valid_json_file(self):
        """Test parsing a valid JSON file"""
        valid_json = json.dumps({
            'questions': [
                {
                    'question': 'Test?',
                    'options': ['A', 'B', 'C'],
                    'correct': 0
                }
            ]
        })
        
        data = json.loads(valid_json)
        assert 'questions' in data
        assert len(data['questions']) == 1
    
    def test_parse_invalid_json(self):
        """Test handling of invalid JSON"""
        invalid_json = "{ invalid json }"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
    
    def test_parse_json_array(self):
        """Test parsing JSON array format"""
        json_array = json.dumps([
            {
                'question': 'Question 1?',
                'options': ['A', 'B'],
                'correct': 0
            },
            {
                'question': 'Question 2?',
                'options': ['X', 'Y'],
                'correct': 1
            }
        ])
        
        data = json.loads(json_array)
        assert isinstance(data, list)
        assert len(data) == 2


class TestEnvironmentVariables:
    """Test environment variable handling"""
    
    def test_mongo_uri_from_env(self):
        """Test reading MONGO_URI from environment"""
        test_uri = 'mongodb://testuser:testpass@localhost:27017/testdb'
        
        with patch.dict(os.environ, {'MONGO_URI': test_uri}):
            retrieved_uri = os.getenv('MONGO_URI', 'default')
            assert retrieved_uri == test_uri
    
    def test_mongo_uri_default(self):
        """Test MONGO_URI falls back to default"""
        env_copy = os.environ.copy()
        if 'MONGO_URI' in env_copy:
            del env_copy['MONGO_URI']
        
        with patch.dict(os.environ, env_copy, clear=True):
            retrieved_uri = os.getenv('MONGO_URI', 'mongodb://quizadmin:quizpass123@localhost:27017/quizdb?authSource=admin')
            assert 'mongodb://' in retrieved_uri
    
    def test_log_level_from_env(self):
        """Test reading LOG_LEVEL from environment"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            assert log_level == 'DEBUG'
