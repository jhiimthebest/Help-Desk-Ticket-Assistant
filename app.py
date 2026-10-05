import ollama, json
import streamlit as st

st.title("🛠️ Help Desk Ticket Assistant")
st.write("Describe the problem, and the AI will sort it and suggest fixes.")

ticket = st.text_area("Ticket", placeholder="Example: My laptop won't connect to Wi-Fi")

if st.button("Analyze") and ticket.strip():
    prompt = f"""You are an IT help desk assistant. Reply ONLY in JSON with keys: category, priority, steps.
- category: one of Account, Network, Hardware, Software, Security
- priority: High if many people are affected or there is a security risk. Medium if one person can't work. Low if they can still work.
- steps: a list of 3 to 5 troubleshooting steps. Never leave it empty.
Ticket: {ticket}"""

    with st.spinner("Thinking..."):
        reply = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}],
                            format="json", options={"temperature": 0})
    result = json.loads(reply["message"]["content"])

    col1, col2 = st.columns(2)
    col1.metric("Category", result.get("category", "?"))
    col2.metric("Priority", result.get("priority", "?"))

    st.subheader("Suggested steps")
    steps = result.get("steps", [])
    if isinstance(steps, str):
        steps = [steps]
    for i, step in enumerate(steps, 1):
        st.write(f"{i}. {step}")