import streamlit as st

# Set the page configuration
st.set_page_config(
    page_title="AI Voice Assistant",
    page_icon="🎙️",
    layout="centered"
)

# Title and description
st.title("🎙️ AI Voice Assistant")
st.write("Welcome to your AI Voice Assistant! Choose how you want to interact: by typing your query or using your voice.")

# Interaction options
st.subheader("Choose Your Input Method")

# Option 1: Guest Typing
st.write("🖊️ **Guest Typing**")
guest_input = st.text_area("Type your query here:", placeholder="Ask me anything...")

# Option 2: Voice Input
st.write("🎤 **Voice Input**")
audio_value = st.audio_input("ask your guestion")

# Process Button
if st.button("Submit"):
    if guest_input.strip():
        st.success("Processing your text query...")
        # Placeholder for AI processing logic for text
        st.write(f"Your query: {guest_input}")
        st.write("Generating a response... (This is where the AI logic will go)")
    elif audio_value is not None:
        st.success("Processing your audio query...")
        # Placeholder for AI processing logic for audio
        st.write("Audio file uploaded successfully! Generating a response... (This is where the AI logic will go)")
    else:
        st.error("Please type a query or upload an audio file!")

# Footer
st.write("---")
st.caption("Developed by [Your Name]. Powered by Streamlit.")