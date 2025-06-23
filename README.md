# TalentScout - AI Hiring Assistant

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hiring-assistant-chatbot-yvdhckkchdjcqxdmxds3ry.streamlit.app/)

An intelligent AI-powered hiring assistant that streamlines the recruitment process through automated candidate screening, technical assessment, and evaluation. Built with Streamlit and LangChain, TalentScout provides a conversational interface for conducting initial candidate interviews and technical evaluations.

## 🌐 Live Demo

The application is deployed and accessible at: **https://hiring-assistant-chatbot-yvdhckkchdjcqxdmxds3ry.streamlit.app/**

## 🚀 Project Overview

TalentScout is a comprehensive AI hiring assistant designed to automate the initial stages of the recruitment process. The application conducts structured conversations with candidates, identifies their technical expertise, generates relevant technical questions, and provides automated evaluations of their responses.

### Key Features

- **Conversational Interface**: WhatsApp-like chat interface for natural candidate interaction
- **Multi-Phase Assessment**: Structured workflow from information collection to technical evaluation
- **AI-Powered Question Generation**: Dynamic creation of technical questions based on identified skills
- **Automated Evaluation**: Intelligent scoring and feedback system for candidate responses
- **Data Persistence**: SQLite database for storing candidate information and assessments
- **Real-time Processing**: Immediate feedback and progression through assessment phases

### Capabilities

1. **Information Collection**: Gathers essential candidate details (name, contact, experience, position, location)
2. **Technology Stack Identification**: Automatically detects and validates mentioned technologies
3. **Technical Question Generation**: Creates relevant questions tailored to candidate's tech stack
4. **Answer Evaluation**: Provides comprehensive assessment with scoring and feedback
5. **Progress Tracking**: Maintains conversation state and assessment progress

## 📋 Installation Instructions

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Groq API key for AI model access

### Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Sri-Vallabh/Hiring-Assistant-Chatbot
   cd Hiring-Assistant-Chatbot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Database Initialization**
   The SQLite database will be automatically initialized when the application starts.

6. **Run the Application**
   ```bash
   streamlit run app.py
   ```

7. **Access the Application**
   Open your browser and navigate to `http://localhost:8501`

### Dependencies

Create a `requirements.txt` file with the following dependencies:

```
streamlit>=1.28.0
langchain-openai>=0.1.0
langchain-core>=0.2.0
langchain>=0.2.0
python-dotenv>=1.0.0
groq>=0.8.0
```

## 🎯 Usage Guide

### For Recruiters/HR Teams

1. **Deploy the Application**: Share the application URL with candidates
2. **Monitor Progress**: Track candidate assessments through the database
3. **Review Results**: Access evaluation scores and feedback for decision-making from the database

### For Candidates

1. **Start Assessment**: Visit the application URL to begin the interview process
2. **Provide Information**: Share basic details when prompted by the AI assistant
3. **Discuss Technical Skills**: Mention your technology stack and experience
4. **Answer Questions**: Respond to generated technical questions
5. **Receive Feedback**: Get immediate evaluation and next steps

### Conversation Flow

```
1. Greeting & Information Collection
   ├── Full Name
   ├── Email Address
   ├── Phone Number
   ├── Years of Experience
   ├── Desired Position
   └── Current Location

2. Technology Stack Discussion
   ├── Identify mentioned technologies
   ├── Validate against known tech stacks
   └── Confirm candidate expertise areas

3. Technical Assessment
   ├── Generate relevant questions
   ├── Present questions one by one
   ├── Collect and process answers
   └── Provide immediate feedback

4. Evaluation & Next Steps
   ├── Compile assessment results
   ├── Generate candidate score
   └── Provide feedback and recommendations
```

## 🔧 Technical Details

### Architecture

- **Frontend**: Streamlit web framework with custom CSS styling
- **Backend**: Python-based logic with LangChain orchestration
- **Database**: SQLite for data persistence
- **AI Integration**: Groq API for language model capabilities
- **State Management**: Streamlit session state for conversation flow

### Core Libraries

| Library | Purpose | Version |
|---------|---------|---------|
| Streamlit | Web application framework | 1.28+ |
| LangChain | AI orchestration and prompting | 0.2+ |
| SQLite3 | Database operations | Built-in |
| Python-dotenv | Environment management | 1.0+ |
| Groq | AI model API access | 0.8+ |

### Database Schema

```sql
-- Candidates table
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    experience INTEGER,
    position TEXT,
    location TEXT,
    tech_stacks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Question ratings table
CREATE TABLE question_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    question TEXT,
    answer TEXT,
    rating INTEGER,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
);
```

### Application Structure

```
talentscout/
├── app.py                 # Main Streamlit application
├── tools.py              # Helper functions and database operations
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── hiring_assistant.db   # SQLite database (auto-generated)
```

## 🎨 Prompt Design

### Information Collection Prompts

The application uses carefully crafted prompts to guide natural conversation:

```python
# Example information collection prompt
"👋 Hi! I'm your AI hiring assistant. Let's get started. What's your full name?"
```

### Technical Question Generation

Dynamic prompts are constructed based on identified technology stacks:

```python
# Structured prompt for question generation
prompt_template = PromptTemplate(
    input_variables=["tech_stack", "experience_level"],
    template="""
    Generate a technical question for a candidate with {experience_level} years 
    of experience in {tech_stack}. The question should be:
    - Appropriate for their experience level
    - Practical and relevant to real-world scenarios
    - Clear and concise
    """
)
```

### Evaluation Prompts

Assessment prompts focus on multiple evaluation criteria:

```python
# Evaluation prompt structure
evaluation_prompt = """
Evaluate the candidate's answer based on:
1. Technical accuracy
2. Depth of understanding
3. Practical experience demonstration
4. Communication clarity

Provide a score (1-10) and constructive feedback.
"""
```

### Prompt Engineering Principles

1. **Clarity**: Clear, unambiguous instructions for the AI model
2. **Context**: Sufficient background information for accurate responses
3. **Structure**: Consistent format for reliable output parsing
4. **Adaptability**: Dynamic prompts that adjust based on candidate responses
5. **Evaluation**: Multi-criteria assessment for comprehensive feedback

## 🚧 Challenges & Solutions

### Challenge 1: Managing Conversation State

**Problem**: Maintaining conversation context across multiple user interactions in a web application.

**Solution**: Implemented comprehensive session state management using Streamlit's built-in session state functionality. Created a structured state machine that tracks conversation phases, collected data, and assessment progress.

```python
# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.info_collected = False
    st.session_state.candidate_data = {}
    # ... additional state variables
```

### Challenge 2: Dynamic Question Generation

**Problem**: Creating relevant technical questions based on diverse technology stacks mentioned by candidates.

**Solution**: Developed a validation system that identifies and categorizes technology stacks, then generates appropriate questions using structured prompts with LangChain's templating system.

```python
# Technology stack validation
def validate_and_extract_stacks(user_input):
    # Extract and validate mentioned technologies
    # Return structured list of confirmed tech stacks
```

### Challenge 3: User Experience Design

**Problem**: Creating an intuitive, engaging interface that feels natural for candidates.

**Solution**: Implemented a WhatsApp-like chat interface with custom CSS styling, message bubbles, and smooth conversation flow that guides users through each assessment phase.

### Challenge 4: Answer Evaluation Accuracy

**Problem**: Providing consistent, fair evaluation of technical answers across different domains.

**Solution**: Developed structured evaluation prompts with multiple assessment criteria, ensuring consistent scoring methodology while maintaining flexibility for different technical domains.

### Challenge 5: Data Persistence

**Problem**: Storing candidate information and assessment results reliably.

**Solution**: Integrated SQLite database with proper schema design, including relationships between candidates and their question responses, with automated database initialization.

## 📝 Code Quality

### Structure & Readability

- **Modular Design**: Separation of concerns with `app.py` for UI logic and `tools.py` for business logic
- **Clear Naming**: Descriptive variable and function names throughout the codebase
- **Consistent Formatting**: Following Python PEP 8 style guidelines
- **Error Handling**: Proper exception handling for API calls and database operations

### Documentation

```python
def insert_candidate(name, email, phone, experience, position, location, tech_stacks):
    """
    Insert a new candidate into the database.
    
    Args:
        name (str): Candidate's full name
        email (str): Email address
        phone (str): Phone number
        experience (int): Years of experience
        position (str): Desired position
        location (str): Current location
        tech_stacks (list): List of technology stacks
    
    Returns:
        int: Candidate ID if successful, None otherwise
    """
```

### Best Practices Implemented

1. **Environment Variables**: Secure API key management using `.env` files
2. **Input Validation**: Sanitization of user inputs and data validation
3. **Session Management**: Proper state handling for web application sessions
4. **Database Integrity**: Foreign key relationships and data consistency
5. **Error Recovery**: Graceful handling of API failures and edge cases

### Version Control

```bash
# Example commit structure
git commit -m "feat: Add technology stack validation system"
git commit -m "fix: Resolve session state persistence issue"
git commit -m "docs: Update README with deployment instructions"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Streamlit team for the excellent web framework
- LangChain developers for AI orchestration tools
- Groq for providing AI model access
- Open source community for inspiration and support

## 📞 Support

For questions, issues, or suggestions, please open an issue in the repository or contact me.

---

**TalentScout** - Revolutionizing the hiring process with AI-powered conversations.