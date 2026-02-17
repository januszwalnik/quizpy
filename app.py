import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from bson.objectid import ObjectId


class DatabaseConnection:
    def __init__(self):
        self.client = None
        self.db = None
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://quizadmin:quizpass123@localhost:27017/quizdb?authSource=admin')
        self.connected = False
        self.connect_async()
    
    def connect_async(self):
        """Connect to MongoDB with retry logic"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client['quizdb']
            self.connected = True
            print("Connected to MongoDB successfully")
        except Exception as e:
            print(f"MongoDB not ready yet, will retry on first use: {e}")
            self.connected = False
            self.db = None
            self.client = None
    
    def connect(self):
        """Ensure connection is established, retry if needed"""
        if self.connected and self.db is not None:
            return True
        
        # Try to connect
        try:
            if not self.client:
                self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
            self.client.admin.command('ping')
            self.db = self.client['quizdb']
            self.connected = True
            print("Connected to MongoDB successfully")
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            self.connected = False
            self.db = None
            self.client = None
            return False
    
    def get_all_questions(self):
        """Fetch all questions from MongoDB"""
        try:
            if not self.connect():
                print("Could not connect to MongoDB")
                return []
            if self.db is None:
                print("Database is None")
                return []
            questions = list(self.db.questions.find().sort('createdAt', -1))
            print(f"Successfully fetched {len(questions)} questions from database")
            return questions
        except Exception as e:
            print(f"Error fetching questions: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def add_question(self, question_text, options, correct_index, explanation=""):
        """Add a new question to MongoDB"""
        try:
            if not self.connect():
                print("Could not connect to MongoDB")
                return False
            if self.db is None:
                print("Database is None")
                return False
            self.db.questions.insert_one({
                'question': question_text,
                'options': options,
                'correct': correct_index,
                'explanation': explanation,
                'createdAt': datetime.now()
            })
            print("Question added successfully")
            return True
        except Exception as e:
            print(f"Error adding question: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_question(self, question_id):
        """Delete a question from MongoDB"""
        try:
            if not self.connect():
                return False
            if self.db is None:
                return False
            from bson.objectid import ObjectId
            result = self.db.questions.delete_one({'_id': ObjectId(question_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting question: {e}")
            return False
    
    def delete_all_questions(self):
        """Delete all questions from MongoDB"""
        try:
            if not self.connect():
                return False
            if self.db is None:
                return False
            result = self.db.questions.delete_many({})
            print(f"Deleted {result.deleted_count} questions")
            return True
        except Exception as e:
            print(f"Error deleting all questions: {e}")
            return False
    
    def update_question(self, question_id, question_text, options, correct_index, explanation=""):
        """Update an existing question in MongoDB"""
        try:
            if not self.connect():
                return False
            if self.db is None:
                return False
            from bson.objectid import ObjectId
            result = self.db.questions.update_one(
                {'_id': ObjectId(question_id)},
                {'$set': {
                    'question': question_text,
                    'options': options,
                    'correct': correct_index,
                    'explanation': explanation,
                    'updatedAt': datetime.now()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating question: {e}")
            return False
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Application")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.bg_color = "#f5f5f5"
        self.primary_color = "#2196F3"
        self.secondary_color = "#1976D2"
        self.accent_color = "#FF6B6B"
        self.text_color = "#212121"
        self.success_color = "#4CAF50"
        
        # Set root background
        self.root.configure(bg=self.bg_color)
        
        # Configure style
        self.setup_styles()
        
        # Database connection
        self.db = DatabaseConnection()
        
        # Variables
        self.quiz_data = []
        self.current_question = 0
        self.score = 0
        self.user_answers = []
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frames
        self.create_start_screen()
    
    def setup_styles(self):
        """Configure modern styling for the app"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.text_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', background=self.bg_color, foreground=self.text_color, font=('Segoe UI', 24, 'bold'))
        style.configure('Subtitle.TLabel', background=self.bg_color, foreground='#666666', font=('Segoe UI', 12))
        
        # Configure buttons
        style.configure('TButton', font=('Segoe UI', 10), padding=10)
        style.map('TButton',
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', self.secondary_color), ('active', self.primary_color)])
        
        # Configure primary button style
        style.configure('Primary.TButton', font=('Segoe UI', 11, 'bold'), padding=12)
        style.map('Primary.TButton',
                  foreground=[('pressed', 'white'), ('active', 'white'), ('disabled', '#999999')],
                  background=[('pressed', self.secondary_color), ('active', self.primary_color), ('disabled', '#e0e0e0')])
        
        # Configure success button style
        style.configure('Success.TButton', font=('Segoe UI', 10, 'bold'), padding=10)
        style.map('Success.TButton',
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', '#388E3C'), ('active', self.success_color)])
        
        # Configure danger button style
        style.configure('Danger.TButton', font=('Segoe UI', 10, 'bold'), padding=10)
        style.map('Danger.TButton',
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', '#C62828'), ('active', self.accent_color)])
        
    def create_start_screen(self):
        """Create the initial screen to load quiz data"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top padding
        ttk.Frame(main_frame, height=40).pack()
        
        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, padx=40)
        
        title = ttk.Label(title_frame, text="Quiz Application", style='Title.TLabel')
        title.pack(pady=10)
        
        desc = ttk.Label(title_frame, text="Select an option to get started", style='Subtitle.TLabel')
        desc.pack(pady=5)
        
        # Divider
        ttk.Frame(main_frame, height=2).pack(fill=tk.X, pady=20)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=40)
        
        # Start Quiz button
        start_btn = ttk.Button(button_frame, text="Start Quiz", command=self.load_quiz_from_db, style='Primary.TButton')
        start_btn.pack(pady=15, fill=tk.X, ipady=10)
        
        # Add New Question button
        add_btn = ttk.Button(button_frame, text="Add New Question", command=self.show_add_question_dialog, style='Primary.TButton')
        add_btn.pack(pady=15, fill=tk.X, ipady=10)
        
        # Import Questions button
        import_btn = ttk.Button(button_frame, text="Import Questions from JSON", command=self.show_import_json_dialog, style='Primary.TButton')
        import_btn.pack(pady=15, fill=tk.X, ipady=10)
        
        # View & Manage Questions button
        view_btn = ttk.Button(button_frame, text="View & Manage Questions", command=self.show_all_questions_dialog, style='Primary.TButton')
        view_btn.pack(pady=15, fill=tk.X, ipady=10)
        
        # Bottom status section
        ttk.Frame(main_frame, height=20).pack()
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=40, pady=20)
        
        status_label = ttk.Label(status_frame, text="✓ Questions loaded from MongoDB", style='Subtitle.TLabel', foreground=self.success_color)
        status_label.pack()
    
    def load_quiz_from_db(self):
        """Load quiz data from MongoDB"""
        try:
            quiz_questions = self.db.get_all_questions()
            
            if not quiz_questions:
                messagebox.showwarning("No Questions", "No questions found in the database.\n\nPlease add some questions first using 'Add New Question'.")
                return
            
            # Convert MongoDB documents to the format expected by the quiz
            self.quiz_data = quiz_questions
            self.current_question = 0
            self.score = 0
            self.user_answers = []
            self.show_question()
        except Exception as e:
            print(f"Error loading quiz: {e}")
            messagebox.showerror("Error", f"Failed to load quiz: {str(e)}")
    
    def show_question(self):
        """Display the current question"""
        self.clear_window()
        
        if self.current_question >= len(self.quiz_data):
            self.show_results()
            return
        
        question_data = self.quiz_data[self.current_question]
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Progress section
        progress_text = f"Question {self.current_question + 1} of {len(self.quiz_data)}"
        progress = ttk.Label(main_frame, text=progress_text, style='Subtitle.TLabel')
        progress.pack(anchor=tk.W, pady=(0, 10))
        
        progress_bar = ttk.Progressbar(
            main_frame,
            length=600,
            mode='determinate',
            value=(self.current_question / len(self.quiz_data)) * 100
        )
        progress_bar.pack(fill=tk.X, pady=(0, 20))
        
        # Question card
        question_label = ttk.Label(
            main_frame,
            text=question_data['question'],
            font=('Segoe UI', 16, 'bold'),
            wraplength=700,
            justify=tk.LEFT
        )
        question_label.pack(anchor=tk.W, pady=(0, 25))
        
        # Radio buttons for options
        self.selected_option = tk.IntVar()
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        for i, option in enumerate(question_data['options']):
            radio = ttk.Radiobutton(
                options_frame,
                text=option,
                variable=self.selected_option,
                value=i
            )
            radio.pack(anchor=tk.W, pady=12)
        
        # Show answer button
        show_answer_btn = ttk.Button(
            main_frame,
            text="Show Correct Answer",
            command=lambda: self.show_answer_popup(question_data),
            style='TButton'
        )
        show_answer_btn.pack(pady=(0, 20), fill=tk.X)
        
        # Navigation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        prev_btn = ttk.Button(
            button_frame,
            text="← Previous",
            command=self.previous_question,
            state=tk.DISABLED if self.current_question == 0 else tk.NORMAL
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = ttk.Button(
            button_frame,
            text="Next →",
            command=self.next_question,
            style='Primary.TButton'
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        submit_btn = ttk.Button(
            button_frame,
            text="Finish Quiz",
            command=self.finish_quiz,
            style='Success.TButton'
        )
        submit_btn.pack(side=tk.LEFT, padx=5)
    
    def next_question(self):
        """Move to the next question"""
        self.user_answers.append(self.selected_option.get())
        self.current_question += 1
        
        if self.selected_option.get() == self.quiz_data[self.current_question - 1]['correct']:
            self.score += 1
        
        self.show_question()
    
    def show_answer_popup(self, question_data):
        """Show a popup with the correct answer and explanation"""
        popup = tk.Toplevel(self.root)
        popup.title("Correct Answer")
        popup.geometry("500x300")
        popup.resizable(True, True)
        
        frame = ttk.Frame(popup, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Correct answer
        correct_idx = question_data['correct']
        correct_answer = question_data['options'][correct_idx]
        
        ttk.Label(frame, text="Correct Answer:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text=f"{correct_idx + 1}: {correct_answer}", font=("Arial", 11, "bold"), foreground="green").pack(anchor=tk.W, pady=(0, 15))
        
        # Explanation
        explanation = question_data.get('explanation', 'No explanation provided')
        ttk.Label(frame, text="Explanation:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        explanation_text = tk.Text(frame, height=10, width=60, font=("Arial", 10), wrap=tk.WORD)
        explanation_text.pack(fill=tk.BOTH, expand=True)
        explanation_text.insert(1.0, explanation)
        explanation_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(frame, text="Close", command=popup.destroy).pack(pady=10)
    
    def previous_question(self):
        """Move to the previous question"""
        if self.current_question > 0:
            self.current_question -= 1
            self.show_question()
    
    def finish_quiz(self):
        """End the quiz and show results"""
        if len(self.user_answers) < self.current_question + 1:
            self.user_answers.append(self.selected_option.get())
            if self.selected_option.get() == self.quiz_data[self.current_question]['correct']:
                self.score += 1
        
        self.show_results()
    
    def show_results(self):
        """Display quiz results"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Results title
        title = ttk.Label(main_frame, text="Quiz Complete!", style='Title.TLabel')
        title.pack(pady=(0, 10))
        
        # Score with color coding
        percentage = (self.score / len(self.quiz_data)) * 100 if self.quiz_data else 0
        score_text = f"Your Score: {self.score}/{len(self.quiz_data)}"
        percentage_text = f"{percentage:.1f}%"
        
        score_label = ttk.Label(main_frame, text=score_text, font=('Segoe UI', 18, 'bold'), foreground=self.primary_color)
        score_label.pack(pady=(0, 5))
        
        percentage_label = ttk.Label(main_frame, text=percentage_text, font=('Segoe UI', 14))
        percentage_label.pack(pady=(0, 20))
        
        # Results frame
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create a scrollable text widget for detailed results
        canvas = tk.Canvas(results_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display each question with user answer
        for i, question_data in enumerate(self.quiz_data):
            user_answer = self.user_answers[i] if i < len(self.user_answers) else -1
            correct = question_data['correct']
            is_correct = user_answer == correct
            
            # Question card with border effect
            card_frame = ttk.Frame(scrollable_frame)
            card_frame.pack(fill=tk.X, pady=8, padx=5)
            
            # Status indicator
            status_symbol = "✓" if is_correct else "✗"
            status_color = self.success_color if is_correct else self.accent_color
            
            question_text = f"{status_symbol} {i+1}. {question_data['question']}"
            question_label = ttk.Label(
                card_frame,
                text=question_text,
                font=('Segoe UI', 11, 'bold'),
                foreground=status_color,
                wraplength=600,
                justify=tk.LEFT
            )
            question_label.pack(anchor=tk.W, pady=(5, 8))
            
            if user_answer >= 0 and user_answer < len(question_data['options']):
                answer_text = f"Your answer: {question_data['options'][user_answer]}"
                answer_label = ttk.Label(
                    card_frame,
                    text=answer_text,
                    foreground=status_color,
                    font=('Segoe UI', 10)
                )
                answer_label.pack(anchor=tk.W, padx=20, pady=3)
            
            if not is_correct:
                correct_text = f"Correct answer: {question_data['options'][correct]}"
                correct_label = ttk.Label(
                    card_frame,
                    text=correct_text,
                    foreground=self.primary_color,
                    font=('Segoe UI', 10, 'bold')
                )
                correct_label.pack(anchor=tk.W, padx=20, pady=3)
            
            # Show explanation if exists
            explanation = question_data.get('explanation', '')
            if explanation:
                explanation_label = ttk.Label(
                    card_frame,
                    text=f"💡 {explanation}",
                    font=('Segoe UI', 9),
                    wraplength=600,
                    justify=tk.LEFT,
                    foreground='#666666'
                )
                explanation_label.pack(anchor=tk.W, padx=20, pady=(8, 5))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=0)
        
        restart_btn = ttk.Button(button_frame, text="Restart Quiz", command=self.load_quiz_from_db, style='Primary.TButton')
        restart_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        home_btn = ttk.Button(button_frame, text="Back to Home", command=self.create_start_screen, style='TButton')
        home_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        exit_btn = ttk.Button(button_frame, text="Exit", command=self.root.quit, style='Danger.TButton')
        exit_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
    
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_add_question_dialog(self):
        """Show dialog to add a new question"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Question")
        dialog.geometry("700x750")
        dialog.resizable(True, True)
        dialog.configure(bg=self.bg_color)
        
        # Create main frame with scrollbar
        canvas = tk.Canvas(dialog, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        frame = ttk.Frame(scrollable_frame, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Add New Question", style='Title.TLabel', font=('Segoe UI', 18, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Question text
        ttk.Label(frame, text="Question:", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        question_text = tk.Text(frame, height=3, width=60, font=("Segoe UI", 10), bg="white", relief=tk.FLAT, bd=1)
        question_text.pack(fill=tk.X, pady=(0, 15))
        
        # Options
        ttk.Label(frame, text="Answer Options (one per line):", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        options_text = tk.Text(frame, height=4, width=60, font=("Segoe UI", 10), bg="white", relief=tk.FLAT, bd=1)
        options_text.pack(fill=tk.X, pady=(0, 15))
        
        # Correct answer
        ttk.Label(frame, text="Correct Answer (option number, starting from 0):", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        correct_frame = ttk.Frame(frame)
        correct_frame.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        correct_var = tk.IntVar(value=0)
        correct_spinbox = ttk.Spinbox(correct_frame, from_=0, to=9, textvariable=correct_var, width=5)
        correct_spinbox.pack(side=tk.LEFT)
        ttk.Label(correct_frame, text="(0-9)", style='Subtitle.TLabel').pack(side=tk.LEFT, padx=10)
        
        # Explanation
        ttk.Label(frame, text="Explanation (optional):", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        explanation_text = tk.Text(frame, height=3, width=60, font=("Segoe UI", 9), bg="white", relief=tk.FLAT, bd=1)
        explanation_text.pack(fill=tk.X, pady=(0, 20))
        
        def save_question():
            question = question_text.get(1.0, tk.END).strip()
            options_text_content = options_text.get(1.0, tk.END).strip()
            options = [opt.strip() for opt in options_text_content.split('\n') if opt.strip()]
            correct_index = correct_var.get()
            explanation = explanation_text.get(1.0, tk.END).strip()
            
            # Validation
            if not question:
                messagebox.showerror("Error", "Question cannot be empty")
                return
            
            if len(options) < 2:
                messagebox.showerror("Error", "At least 2 options are required")
                return
            
            if correct_index < 0 or correct_index >= len(options):
                messagebox.showerror("Error", f"Correct answer must be between 0 and {len(options)-1}")
                return
            
            # Save to database
            if self.db.add_question(question, options, correct_index, explanation):
                messagebox.showinfo("Success", "Question added successfully!")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to add question to database")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=0)
        
        ttk.Button(button_frame, text="Save", command=save_question, style='Success.TButton').pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='TButton').pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_closing(self):
        """Handle window closing"""
        self.db.close()
        self.root.destroy()
    
    def show_all_questions_dialog(self):
        """Show dialog to view and manage all questions"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Questions")
        dialog.geometry("1100x750")
        dialog.resizable(True, True)
        dialog.configure(bg=self.bg_color)
        
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="All Questions in Database", style='Title.TLabel', font=('Segoe UI', 18, 'bold')).pack(anchor=tk.W, side=tk.LEFT)
        
        # Action buttons
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(anchor=tk.E, side=tk.RIGHT, fill=tk.X, expand=True)
        
        def export_to_json():
            questions = self.db.get_all_questions()
            if not questions:
                messagebox.showwarning("No Questions", "No questions to export")
                return
            
            # Convert to JSON-serializable format
            export_data = []
            for q in questions:
                export_data.append({
                    "question": q.get('question', ''),
                    "options": q.get('options', []),
                    "correct": q.get('correct', 0),
                    "explanation": q.get('explanation', '')
                })
            
            # Create JSON string
            json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Show dialog with JSON
            export_dialog = tk.Toplevel(self.root)
            export_dialog.title("Export Questions as JSON")
            export_dialog.geometry("800x600")
            export_dialog.resizable(True, True)
            export_dialog.configure(bg=self.bg_color)
            
            frame = ttk.Frame(export_dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            ttk.Label(frame, text="Copy this JSON to use in another instance:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
            
            # Text area with JSON
            json_text = tk.Text(frame, height=20, width=90, font=("Courier", 9), wrap=tk.NONE, bg="white", relief=tk.FLAT, bd=1)
            json_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            json_text.insert(1.0, json_string)
            json_text.config(state=tk.DISABLED)
            
            # Scrollbars
            vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=json_text.yview)
            hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=json_text.xview)
            json_text.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            # Buttons
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=10)
            
            def copy_to_clipboard():
                export_dialog.clipboard_clear()
                export_dialog.clipboard_append(json_string)
                messagebox.showinfo("Success", "JSON copied to clipboard!")
            
            ttk.Button(btn_frame, text="Copy to Clipboard", command=copy_to_clipboard, style='Success.TButton').pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            ttk.Button(btn_frame, text="Close", command=export_dialog.destroy, style='TButton').pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        def remove_all():
            if messagebox.askyesno("Confirm", "Are you sure you want to delete ALL questions? This cannot be undone!"):
                if self.db.delete_all_questions():
                    messagebox.showinfo("Success", "All questions deleted!")
                    dialog.destroy()
                    self.show_all_questions_dialog()
                else:
                    messagebox.showerror("Error", "Failed to delete questions")
        
        ttk.Button(button_frame, text="Export as JSON", command=export_to_json, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove All", command=remove_all, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Fetch all questions
        questions = self.db.get_all_questions()
        
        if not questions:
            ttk.Label(scrollable_frame, text="No questions found in database", font=("Segoe UI", 12), foreground='#999999').pack(pady=20)
        else:
            for idx, q in enumerate(questions):
                # Create a frame for each question with modern styling
                q_frame = ttk.Frame(scrollable_frame)
                q_frame.pack(fill=tk.X, pady=8, padx=5)
                
                # Question number and text
                question_label = ttk.Label(
                    q_frame, 
                    text=f"Q{idx + 1}: {q.get('question', 'N/A')}", 
                    font=("Segoe UI", 11, "bold"),
                    wraplength=800,
                    justify=tk.LEFT,
                    foreground=self.primary_color
                )
                question_label.pack(anchor=tk.W, pady=(0, 8))
                
                # Options
                options_text = "\n".join([f"  {i}: {opt}" for i, opt in enumerate(q.get('options', []))])
                ttk.Label(q_frame, text=options_text, font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 5))
                
                # Correct answer
                correct_idx = q.get('correct', 0)
                correct_text = f"✓ Correct: {correct_idx} - {q.get('options', ['N/A'])[correct_idx]}"
                ttk.Label(q_frame, text=correct_text, font=("Segoe UI", 9, "bold"), foreground=self.success_color).pack(anchor=tk.W, pady=(0, 5))
                
                # Explanation if exists
                explanation = q.get('explanation', '')
                if explanation:
                    ttk.Label(q_frame, text=f"💡 {explanation}", font=("Segoe UI", 9), foreground='#666666', wraplength=800, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 8))
                
                # Buttons frame
                btn_frame = ttk.Frame(q_frame)
                btn_frame.pack(anchor=tk.E, pady=(5, 0), fill=tk.X)
                
                # Edit button
                def edit_question(question_id=q.get('_id'), question_data=q):
                    self.show_edit_question_dialog(question_id, question_data)
                    dialog.destroy()
                
                edit_btn = ttk.Button(btn_frame, text="✏ Edit", command=edit_question, style='Primary.TButton')
                edit_btn.pack(side=tk.LEFT, padx=3, pady=5)
                
                # Delete button
                def delete_question(question_id=q.get('_id')):
                    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this question?"):
                        if self.db.delete_question(question_id):
                            messagebox.showinfo("Success", "Question deleted successfully!")
                            dialog.destroy()
                            self.show_all_questions_dialog()
                        else:
                            messagebox.showerror("Error", "Failed to delete question")
                
                delete_btn = ttk.Button(btn_frame, text="🗑 Delete", command=delete_question, style='Danger.TButton')
                delete_btn.pack(side=tk.LEFT, padx=3, pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=dialog.destroy, style='TButton')
        close_btn.pack(pady=10, anchor=tk.E)
    
    def show_edit_question_dialog(self, question_id, question_data):
        """Show dialog to edit an existing question"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Question")
        dialog.geometry("700x750")
        dialog.resizable(True, True)
        dialog.configure(bg=self.bg_color)
        
        # Create main frame with scrollbar
        canvas = tk.Canvas(dialog, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        frame = ttk.Frame(scrollable_frame, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Edit Question", style='Title.TLabel', font=('Segoe UI', 18, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Question text
        ttk.Label(frame, text="Question:", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        question_text = tk.Text(frame, height=3, width=60, font=("Segoe UI", 10), bg="white", relief=tk.FLAT, bd=1)
        question_text.pack(fill=tk.X, pady=(0, 15))
        question_text.insert(1.0, question_data.get('question', ''))
        
        # Options
        ttk.Label(frame, text="Answer Options (one per line):", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        options_text = tk.Text(frame, height=4, width=60, font=("Segoe UI", 10), bg="white", relief=tk.FLAT, bd=1)
        options_text.pack(fill=tk.X, pady=(0, 15))
        options_str = '\n'.join(question_data.get('options', []))
        options_text.insert(1.0, options_str)
        
        # Correct answer
        ttk.Label(frame, text="Correct Answer (option number, starting from 0):", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        correct_frame = ttk.Frame(frame)
        correct_frame.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        correct_var = tk.IntVar(value=question_data.get('correct', 0))
        correct_spinbox = ttk.Spinbox(correct_frame, from_=0, to=9, textvariable=correct_var, width=5)
        correct_spinbox.pack(side=tk.LEFT)
        ttk.Label(correct_frame, text="(0-9)", style='Subtitle.TLabel').pack(side=tk.LEFT, padx=10)
        
        # Explanation
        ttk.Label(frame, text="Explanation (optional):", style='TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        explanation_text = tk.Text(frame, height=3, width=60, font=("Segoe UI", 9), bg="white", relief=tk.FLAT, bd=1)
        explanation_text.pack(fill=tk.X, pady=(0, 20))
        explanation_text.insert(1.0, question_data.get('explanation', ''))
        
        def save_question():
            question = question_text.get(1.0, tk.END).strip()
            options_text_content = options_text.get(1.0, tk.END).strip()
            options = [opt.strip() for opt in options_text_content.split('\n') if opt.strip()]
            correct_index = correct_var.get()
            explanation = explanation_text.get(1.0, tk.END).strip()
            
            # Validation
            if not question:
                messagebox.showerror("Error", "Question cannot be empty")
                return
            
            if len(options) < 2:
                messagebox.showerror("Error", "At least 2 options are required")
                return
            
            if correct_index < 0 or correct_index >= len(options):
                messagebox.showerror("Error", f"Correct answer must be between 0 and {len(options)-1}")
                return
            
            # Update in database
            if self.db.update_question(question_id, question, options, correct_index, explanation):
                messagebox.showinfo("Success", "Question updated successfully!")
                dialog.destroy()
                self.show_all_questions_dialog()
            else:
                messagebox.showerror("Error", "Failed to update question")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=0)
        
        ttk.Button(button_frame, text="Save Changes", command=save_question, style='Success.TButton').pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='TButton').pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_import_json_dialog(self):
        """Show dialog to import questions from JSON"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Questions from JSON")
        dialog.geometry("850x650")
        dialog.resizable(True, True)
        dialog.configure(bg=self.bg_color)
        
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Import Questions from JSON", style='Title.TLabel', font=('Segoe UI', 18, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Instructions
        ttk.Label(main_frame, text="Paste a JSON array of questions below:", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(0, 15))
        
        # Create a frame for text editor with line numbers
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Line numbers widget
        line_numbers = tk.Text(text_frame, width=4, padx=3, takefocus=0, border=0, background='#e0e0e0', state='disabled', font=("Courier", 9))
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text area for JSON with scrollbar
        json_text = tk.Text(text_frame, height=20, font=("Courier", 9), bg="white", relief=tk.FLAT, bd=1)
        json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=json_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        json_text.config(yscrollcommand=scrollbar.set)
        
        # Update line numbers when text changes
        def update_line_numbers(event=None):
            line_numbers.config(state='normal')
            line_numbers.delete(1.0, tk.END)
            lines = json_text.get(1.0, tk.END).count('\n')
            line_nums = '\n'.join(str(i) for i in range(1, lines + 1))
            line_numbers.insert(1.0, line_nums)
            line_numbers.config(state='disabled')
            if event:
                return 'break' if str(event.keysym).startswith('Control') else None
        
        # Bind the update function for text modification (but not keyboard shortcuts)
        json_text.bind('<MouseWheel>', update_line_numbers)
        json_text.bind('<Button-4>', update_line_numbers)
        json_text.bind('<Button-5>', update_line_numbers)
        json_text.bind('<KeyRelease>', lambda e: dialog.after(1, update_line_numbers) if str(e.keysym) not in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R'] else None)
        
        # Enable standard keyboard shortcuts explicitly
        def select_all(event=None):
            json_text.tag_add(tk.SEL, "1.0", tk.END)
            json_text.mark_set(tk.INSERT, "1.0")
            json_text.see(tk.INSERT)
            return 'break'
        
        json_text.bind('<Control-a>', select_all)
        json_text.bind('<Control-A>', select_all)
        
        # Example format
        example = """[
  {
    "question": "What is 2+2?",
    "options": ["3", "4", "5", "6"],
    "correct": 1,
    "explanation": "2 plus 2 equals 4"
  },
  {
    "question": "What is the capital of France?",
    "options": ["London", "Berlin", "Paris", "Madrid"],
    "correct": 2,
    "explanation": "Paris is the capital and largest city of France"
  }
]"""
        json_text.insert(1.0, example)
        update_line_numbers()
        
        def import_questions():
            json_content = json_text.get(1.0, tk.END).strip()
            
            if not json_content:
                messagebox.showerror("Error", "Please paste JSON content")
                return
            
            try:
                questions = json.loads(json_content)
                
                if not isinstance(questions, list):
                    messagebox.showerror("Error", "JSON must be an array of questions")
                    return
                
                if len(questions) == 0:
                    messagebox.showerror("Error", "JSON array cannot be empty")
                    return
                
                # Validate and add questions
                added_count = 0
                for i, q in enumerate(questions):
                    # Validate question structure
                    if not all(key in q for key in ['question', 'options', 'correct']):
                        messagebox.showerror("Error", f"Question {i+1} is missing required fields (question, options, correct)")
                        return
                    
                    if not isinstance(q['options'], list) or len(q['options']) < 2:
                        messagebox.showerror("Error", f"Question {i+1} must have at least 2 options")
                        return
                    
                    if not isinstance(q['correct'], int) or q['correct'] < 0 or q['correct'] >= len(q['options']):
                        messagebox.showerror("Error", f"Question {i+1} has invalid 'correct' index")
                        return
                    
                    # Add to database
                    if self.db.add_question(q['question'], q['options'], q['correct'], q.get('explanation', '')):
                        added_count += 1
                
                messagebox.showinfo("Success", f"Successfully imported {added_count} question(s)!")
                dialog.destroy()
            
            except json.JSONDecodeError as e:
                messagebox.showerror("JSON Error", f"Invalid JSON format at line {e.lineno}, col {e.colno}: {e.msg}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import questions: {str(e)}")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=0)
        
        ttk.Button(button_frame, text="Import", command=import_questions, style='Success.TButton').pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='TButton').pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)


def main():
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
