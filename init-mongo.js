// Initialize MongoDB with default questions
db = db.getSiblingDB('quizdb');

db.questions.insertMany([
  {
    "question": "What is the capital of France?",
    "options": ["London", "Berlin", "Paris", "Madrid"],
    "correct": 2,
    "createdAt": new Date()
  },
  {
    "question": "Which planet is known as the Red Planet?",
    "options": ["Venus", "Mars", "Jupiter", "Saturn"],
    "correct": 1,
    "createdAt": new Date()
  },
  {
    "question": "What is 2 + 2?",
    "options": ["3", "4", "5", "6"],
    "correct": 1,
    "createdAt": new Date()
  },
  {
    "question": "Who wrote Romeo and Juliet?",
    "options": ["Jane Austen", "William Shakespeare", "Charles Dickens", "Mark Twain"],
    "correct": 1,
    "createdAt": new Date()
  },
  {
    "question": "What is the largest ocean on Earth?",
    "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
    "correct": 3,
    "createdAt": new Date()
  }
]);

// Create index on createdAt for sorting
db.questions.createIndex({ "createdAt": -1 });
