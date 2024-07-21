# PDF Chat and Exam Simulator

## Overview
This application allows users to interact with multiple PDF documents through a chat interface and participate in an exam simulation based on the PDF content.

## Features
- Load and process multiple PDF files from a selected directory
- Chat interface for asking questions about PDF content
- Exam simulation with auto-generated questions in Italian
- Interactive exam experience with immediate feedback
- Exam summary showing correct and incorrect answers

## Requirements
- Python 3.7+
- PyQt6
- langchain, langchain_community, langchain_openai
- openai
- faiss-cpu

## Installation
1. Clone the repository
2. Install required packages:
   pip install PyQt6 langchain langchain_community langchain_openai openai faiss-cpu
3. Ensure you have an OpenAI API key (https://platform.openai.com/api-keys)

## Usage
1. Run the application
2. Enter your OpenAI API key when prompted
3. Click "Select Directory" to choose a folder with PDFs
4. After processing:
   - Ask questions about PDF content
   - Start exam simulation: type "exam simulation" or "simulazione di esame"
5. During exam:
   - Answer with 'a', 'b', 'c', or 'd'
   - Type 'next' for the next question
   - Type 'exit' to end early
6. View exam performance summary at the end

## Note
Exam questions are generated in Italian. Ensure PDFs contain relevant Italian content for best results.

## Troubleshooting
- Verify all dependencies are correctly installed
- Check OpenAI API key validity
- Ensure PDFs are readable and contain relevant content

## Contributing
Contributions, issues, and feature requests are welcome. Check the issues page on the repository.


## Author
Marco "Techcraft"

For support or inquiries, please open an issue in the repository.