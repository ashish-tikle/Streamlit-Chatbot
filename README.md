# 🤖 Streamlit Chatbot with LiteLLM & Gemini

A modern, feature-rich chatbot application built with Streamlit, LiteLLM, and Google's Gemini-1.5-Flash model.

## ✨ Features

- 💬 **Streaming Responses**: Real-time response generation for better user experience
- 📝 **Chat History**: Maintains conversation context throughout the session
- 🎛️ **Adjustable Settings**: Temperature slider to control response creativity
- 🎨 **Clean UI**: Modern, responsive interface with chat bubbles
- 🔒 **Secure**: API keys managed through environment variables
- ⚡ **Fast**: Powered by Google's Gemini-1.5-Flash model
- 🛠️ **Modular**: Clean separation between UI and backend logic

## 📋 Prerequisites

- Python 3.8 or higher
- Google AI API key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
cd streamlit-chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```
GOOGLE_API_KEY=your_actual_api_key_here
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📁 Project Structure

```
streamlit-chatbot/
├── app.py                      # Main Streamlit UI application
├── backend.py                  # LLM wrapper using LiteLLM
├── prompts/
│   └── system_prompt.txt      # System prompt configuration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🎯 Usage

### Basic Chat

1. Type your message in the chat input at the bottom
2. Press Enter or click Send
3. Watch as the AI responds in real-time

### Adjust Settings

- Use the **Temperature slider** in the sidebar to control response randomness:
  - Lower values (0.0-0.5): More focused and deterministic
  - Medium values (0.5-1.0): Balanced creativity
  - Higher values (1.0-2.0): More creative and varied

### Clear Chat History

Click the **"🗑️ Clear Chat"** button in the sidebar to start a fresh conversation.

## 🔧 Customization

### Change the System Prompt

Edit `prompts/system_prompt.txt` to customize the AI's behavior and personality.

### Use a Different Model

In `backend.py`, modify the default model:

```python
def __init__(self, model: str = "gemini/gemini-1.5-flash", temperature: float = 0.7):
```

LiteLLM supports many models. See [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for options.

### Customize the UI

Modify the CSS in `app.py` to change colors, fonts, and layout:

```python
st.markdown("""
<style>
    /* Your custom CSS here */
</style>
""", unsafe_allow_html=True)
```

## 🏗️ Architecture

### Backend (`backend.py`)

- **ChatBackend Class**: Handles all LLM interactions
- **generate_response()**: Main function for generating responses
- **Error Handling**: Graceful handling of API failures
- **Streaming Support**: Yields response chunks for real-time display

### Frontend (`app.py`)

- **Session State Management**: Maintains chat history across interactions
- **Streaming UI**: Displays responses as they're generated
- **Settings Panel**: Sidebar with configurable parameters
- **Error Display**: User-friendly error messages

## 🔐 Security Best Practices

- ✅ API keys stored in `.env` file (not committed to version control)
- ✅ Environment variables loaded securely
- ✅ No hardcoded credentials
- ✅ `.env.example` provided for reference

## 🐛 Troubleshooting

### "GOOGLE_API_KEY not found" Error

Make sure you've:
1. Created a `.env` file in the project root
2. Added your API key: `GOOGLE_API_KEY=your_key_here`
3. Restarted the Streamlit application

### Import Errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### API Rate Limits

If you encounter rate limit errors, wait a moment and try again. Consider upgrading your API plan if needed.

## 📚 Dependencies

- **Streamlit**: Web application framework
- **LiteLLM**: Unified interface for multiple LLM providers
- **python-dotenv**: Environment variable management

## 🤝 Contributing

Feel free to fork this project and customize it for your needs!

## 📄 License

This project is open source and available for personal and commercial use.

## 🔗 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)

## 💡 Tips

- Start with a temperature of 0.7 for balanced responses
- Use lower temperatures (0.2-0.5) for factual, consistent answers
- Use higher temperatures (0.8-1.2) for creative tasks
- Clear chat history when switching topics for better context

---

**Enjoy chatting with your AI assistant! 🚀**
