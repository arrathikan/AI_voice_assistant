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
st.write("Use your microphone to interact with the assistant.")
if st.button("Start Recording"):
    st.info("Voice input functionality is coming soon!")

# Process Button
if st.button("Submit"):
    if guest_input.strip():
        st.success("Processing your query...")
        # Placeholder for AI processing logic
        st.write(f"Your query: {guest_input}")
        st.write("Generating a response... (This is where the AI logic will go)")
    else:
        st.error("Please type a query or use the voice input option!")

# Footer
st.write("---")
st.caption("Developed by [Your Name]. Powered by Streamlit.")