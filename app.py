import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import openai
import os
from dotenv import load_dotenv

# ----------------------
# Load Environment Variables
# ----------------------
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
openai.api_key = os.getenv("OPENAI_API_KEY")
PDF_PATH = os.getenv("PDF_PATH")
WEBSITE_URL = os.getenv("WEBSITE_URL")

# ----------------------
# Functions
# ----------------------

def send_email(name, email, contact_no, area_of_interest):
    subject = "New Student Profile Submission"
    body = f"""
    New Student Profile Submitted:

    Name: {name}
    Email: {email}
    Contact No.: {contact_no}
    Area of Interest: {area_of_interest}
    """
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = RECEIVER_EMAIL
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        st.success("Profile submitted successfully!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

def extract_pdf_text(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def scrape_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"Error scraping website: {e}"

def chat_with_ai(user_question, website_text, pdf_text, chat_history):
    combined_context = f"Website Content:\n{website_text}\n\nPDF Content:\n{pdf_text}"
    messages = [{"role": "system", "content": "You are a helpful assistant. Use the provided content."}]
    for entry in chat_history:
        messages.append({"role": "user", "content": entry['user']})
        messages.append({"role": "assistant", "content": entry['bot']})
    messages.append({"role": "user", "content": f"{combined_context}\n\nQuestion: {user_question}"})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=False
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating response: {e}"

# ----------------------
# Streamlit UI
# ----------------------

# Apply CSS for 70% width
st.set_page_config(page_title="AIByTec Student Chatbot", layout="wide")
st.markdown(
    """
    <style>
    .main {
        max-width: 70%;
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state['page'] = 'form'
if "chat_history" not in st.session_state:
    st.session_state['chat_history'] = []

# Page: Form Submission
if st.session_state['page'] == 'form':
    st.subheader("Hi! Welcome to AIByTec")
    # st.subheader("Submit Your Profile or Start Chatting Directly")

    # Profile Form
    st.markdown('<p style="font-size: 22px;"><b>Submit Your Profile</b></p>', unsafe_allow_html=True)
    # st.markdown("### Submit Your Profile")
    with st.form(key="profile_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        contact_no = st.text_input("Contact No.")
        area_of_interest = st.text_input("Area of Interest")
        submitted = st.form_submit_button("Submit Profile")
        if submitted:
            if name and email and contact_no and area_of_interest:
                send_email(name, email, contact_no, area_of_interest)
                st.session_state['page'] = 'chat'
                st.rerun()
            else:
                st.warning("Please fill out all fields.")

    # st.markdown("---")
    st.markdown("### Skip the Form")
    if st.button("Start Chat with AI Chatbot"):
        st.session_state['page'] = 'chat'
        st.rerun()

# Page: Chatbot Interface
elif st.session_state['page'] == 'chat':
    st.title("AI Chatbot Interface")

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for entry in st.session_state['chat_history']:
            st.markdown(f"**You:** {entry['user']}")
            st.markdown(f"**AI:** {entry['bot']}")

    # Load website and PDF content
    pdf_text = extract_pdf_text(PDF_PATH) if os.path.exists(PDF_PATH) else "PDF file not found."
    website_text = scrape_website(WEBSITE_URL)

    # Input bar for chatbot
    user_input = st.text_input("Ask a question", key="user_input_chat")
    if user_input:
        with st.spinner("AI is responding..."):
            bot_response = chat_with_ai(user_input, website_text, pdf_text, st.session_state['chat_history'])
        st.session_state['chat_history'].append({"user": user_input, "bot": bot_response})
        st.rerun()
