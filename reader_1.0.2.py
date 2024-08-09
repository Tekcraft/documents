import os
import sys
import time
import random
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit, QFileDialog, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

VERSION = "1.0.2"

class ChatInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.llm = None  # Language model
        self.db = None  # Vector database
        self.all_chunks = []  # All text chunks from PDFs
        self.pdf_count = 0  # Number of PDFs processed
        self.current_exam_question = 0  # Current question in exam simulation
        self.exam_questions = []  # List of exam questions
        self.wrong_answers = []  # List of wrong answers in exam simulation
        self.api_key = self.get_api_key()  # Get OpenAI API key from user
        self.initUI()  # Initialize the user interface

    def get_api_key(self):
        api_key, ok = QInputDialog.getText(self, f'OpenAI API Key - v{VERSION}', 'Enter your OpenAI API key:')
        if ok and api_key:
            os.environ['OPENAI_API_KEY'] = api_key
            return api_key
        else:
            QMessageBox.critical(self, 'Error', 'API key is required to use this application.')
            sys.exit()

    def initUI(self):
        layout = QVBoxLayout()

        self.select_dir_button = QPushButton('Select Directory')
        self.select_dir_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_button)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Enter your question here")
        self.question_input.returnPressed.connect(self.ask_question)
        input_layout.addWidget(self.question_input)

        self.ask_button = QPushButton('Ask')
        self.ask_button.clicked.connect(self.ask_question)
        input_layout.addWidget(self.ask_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)
        self.setWindowTitle(f'PDF Chat - v{VERSION}')
        self.setGeometry(300, 300, 600, 400)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.process_directory(directory)

    def process_directory(self, directory):
        self.chat_area.append(f"Processing directory: {directory}")
        QApplication.processEvents()

        pdf_files = self.find_pdf_files(directory)
        if not pdf_files:
            self.chat_area.append("No PDF files found in the selected directory.")
            return

        self.pdf_count = len(pdf_files)
        self.chat_area.append(f"Found {self.pdf_count} PDF files.")
        QApplication.processEvents()

        documents = []
        for pdf_file in pdf_files:
            self.chat_area.append(f"Processing file: {pdf_file}")
            QApplication.processEvents()
            loader = PyPDFLoader(pdf_file)
            documents.extend(loader.load())

        self.chat_area.append("Splitting text into chunks...")
        QApplication.processEvents()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.all_chunks = text_splitter.split_documents(documents)

        self.chat_area.append("Creating embeddings...")
        QApplication.processEvents()
        embeddings = OpenAIEmbeddings()
        
        self.chat_area.append("Creating search index...")
        QApplication.processEvents()
        self.db = FAISS.from_documents(self.all_chunks, embeddings)

        self.chat_area.append("Initializing language model...")
        QApplication.processEvents()
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)

        self.chat_area.append(f"System ready for questions! {self.pdf_count} PDF documents loaded.")
        self.select_dir_button.setEnabled(False)
        self.question_input.setEnabled(True)
        self.ask_button.setEnabled(True)

    def find_pdf_files(self, directory):
        pdf_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files

    def ask_question(self):
        if not self.llm or not self.db:
            self.chat_area.append("Please select a directory with PDF files first.")
            return

        query = self.question_input.text()
        if query:
            self.chat_area.append(f"\nQuestion: {query}")
            QApplication.processEvents()

            try:
                start_time = time.time()

                if "simulazione di esame" in query.lower() or "exam simulation" in query.lower():
                    self.chat_area.append("Starting exam simulation...")
                    self.generate_exam_simulation()
                else:
                    self.answer_question(query)

                end_time = time.time()
                self.chat_area.append(f"Processing time: {end_time - start_time:.2f} seconds")

            except Exception as e:
                self.chat_area.append(f"An error occurred: {str(e)}")

            self.question_input.clear()

    def generate_exam_simulation(self):
        num_questions = 30
        chunks_per_question = 2
        selected_chunks = random.sample(self.all_chunks, min(num_questions * chunks_per_question, len(self.all_chunks)))

        prompt_template = f"""Crea una domanda d'esame a scelta multipla basata sulle seguenti informazioni. 
        La domanda deve avere 4 possibili risposte, di cui solo una è corretta.

        Informazioni:
        {{context}}

        Istruzioni:
        1. Non creare domande sugli autori dei documenti o su chi ha scritto il testo.
        2. Concentrati sul contenuto e sui concetti presenti nelle informazioni fornite.
        3. Evita domande su dettagli bibliografici o editoriali.
        4. Non menzionare o fare domande su Elisa Grimi, Giuseppe Reale, o qualsiasi altro nome che potrebbe essere l'autore di un PDF.

        Formato della risposta:
        [Domanda]
        a) [Opzione A]
        b) [Opzione B]
        c) [Opzione C]
        d) [Opzione D]
        Risposta corretta: [a/b/c/d]

        Assicurati che la "Risposta corretta:" sia una singola lettera minuscola (a, b, c, o d) senza spazi aggiuntivi.

        Crea una domanda d'esame in italiano:"""

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["context"])
        llm_chain = LLMChain(llm=self.llm, prompt=PROMPT)

        self.exam_questions = []
        for i in range(0, len(selected_chunks), chunks_per_question):
            chunk = " ".join([c.page_content for c in selected_chunks[i:i+chunks_per_question]])
            question = llm_chain.run(context=chunk)
            self.exam_questions.append(question)
            self.chat_area.append(f"Question {len(self.exam_questions)} generated")
            QApplication.processEvents()

        self.current_exam_question = 0
        self.wrong_answers = []
        self.show_next_exam_question()

    def show_next_exam_question(self):
        if self.current_exam_question < len(self.exam_questions):
            question = self.exam_questions[self.current_exam_question]
            self.chat_area.append(f"\nQuestion {self.current_exam_question + 1} of {len(self.exam_questions)}:")
            for line in question.split('\n'):
                if not line.startswith('Risposta corretta:'):
                    self.chat_area.append(line)
            self.chat_area.append("\nEnter your answer (a, b, c, d), 'next' for the next question, or 'exit' to end the simulation:")
            self.question_input.setPlaceholderText("Enter your answer here")
            self.ask_button.clicked.disconnect()
            self.ask_button.clicked.connect(self.check_exam_answer)
            self.question_input.returnPressed.disconnect()
            self.question_input.returnPressed.connect(self.check_exam_answer)
        else:
            self.reset_exam()

    def check_exam_answer(self):
        answer = self.question_input.text().lower().strip()
        if answer == 'exit':
            self.chat_area.append("Ending exam simulation early.")
            self.mark_remaining_questions_as_wrong()
            self.reset_exam()
        elif answer == 'next' or answer == '':
            self.mark_question_as_wrong("No answer provided")
            self.current_exam_question += 1
            self.show_next_exam_question()
        elif answer in ['a', 'b', 'c', 'd']:
            current_question = self.exam_questions[self.current_exam_question]
            correct_answer = ''
            for line in current_question.split('\n'):
                if line.startswith('Risposta corretta:'):
                    correct_answer = line.split(':')[1].strip().lower()
                    break
            
            if answer == correct_answer:
                self.chat_area.append(f"Correct! The answer is: {correct_answer}")
            else:
                self.chat_area.append(f"Wrong. The correct answer was: {correct_answer}")
                self.mark_question_as_wrong(answer)
            
            self.current_exam_question += 1
            self.show_next_exam_question()
        else:
            self.chat_area.append("Please enter 'a', 'b', 'c', 'd', 'next', or 'exit'.")
        self.question_input.clear()

    def mark_question_as_wrong(self, user_answer):
        current_question = self.exam_questions[self.current_exam_question]
        correct_answer = ''
        for line in current_question.split('\n'):
            if line.startswith('Risposta corretta:'):
                correct_answer = line.split(':')[1].strip().lower()
                break
        self.wrong_answers.append((self.current_exam_question, current_question, user_answer, correct_answer))

    def mark_remaining_questions_as_wrong(self):
        for i in range(self.current_exam_question, len(self.exam_questions)):
            self.mark_question_as_wrong("No answer provided")

    def reset_exam(self):
        self.chat_area.append(f"\nExam simulation completed! (v{VERSION})")
        if self.wrong_answers:
            self.chat_area.append("\nWrong answers:")
            for i, question, user_answer, correct_answer in self.wrong_answers:
                self.chat_area.append(f"\nQuestion {i+1}:")
                self.chat_area.append(question)
                self.chat_area.append(f"Your answer: {user_answer}")
                self.chat_area.append(f"Correct answer: {correct_answer}")
        
        total_questions = len(self.exam_questions)
        correct_answers = total_questions - len(self.wrong_answers)
        
        self.chat_area.append(f"\nYou answered {total_questions} out of {total_questions} questions.")
        self.chat_area.append(f"Correct answers: {correct_answers}")
        self.chat_area.append(f"Wrong answers: {len(self.wrong_answers)}")
        
        if total_questions > 0:
            vote = round((correct_answers / total_questions) * 30)
            vote = max(1, min(30, vote))  # Ensure vote is between 1 and 30
            self.chat_area.append(f"\nYour vote: {vote}/30")
            
            if vote > 18:
                result = "PASSED"
            elif vote < 18:
                result = "FAILED"
            else:  # vote == 18
                result = "PASSED"
            
            self.chat_area.append(f"Exam result: {result}")
        
        self.current_exam_question = 0
        self.exam_questions = []
        self.wrong_answers = []
        self.question_input.setPlaceholderText("Enter your question here")
        self.ask_button.clicked.disconnect()
        self.ask_button.clicked.connect(self.ask_question)
        self.question_input.returnPressed.disconnect()
        self.question_input.returnPressed.connect(self.ask_question)

    def answer_question(self, query):
        docs = self.db.similarity_search(query, k=4)
        context = " ".join([doc.page_content for doc in docs])

        prompt_template = """Use the following information to answer the user's question. 
        If you don't find sufficient information to answer, say that you don't have enough information.

        Information:
        {context}

        Question: {question}

        Answer:"""

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        llm_chain = LLMChain(llm=self.llm, prompt=PROMPT)

        result = llm_chain.run(context=context, question=query)
        self.chat_area.append(f"Answer: {result}")
        self.chat_area.append(f"Sources: {[doc.metadata.get('source', 'Unknown') for doc in docs]}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_interface = ChatInterface()
    chat_interface.show()
    sys.exit(app.exec())