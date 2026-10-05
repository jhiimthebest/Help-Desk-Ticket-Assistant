import ollama, json, csv, os, uuid
from datetime import datetime
import streamlit as st
from groq import Groq

QUEUE_FILE = "queue.csv"
FIELDS = ["id", "time", "ticket", "category", "priority", "steps", "feedback"]

# Idea 1: example tickets with the right answers, so the AI learns the pattern
EXAMPLES = """Examples:
Ticket: Nobody in the building can reach the internet
{"category": "Network", "priority": "High", "steps": ["Check if the main router and firewall are online", "Check the ISP for outages", "Restart the core network equipment"]}

Ticket: My mouse double-clicks on its own
{"category": "Hardware", "priority": "Low", "steps": ["Try a different USB port", "Test with another mouse", "Replace the mouse if it keeps happening"]}

Ticket: I forgot my password and can't log in
{"category": "Account", "priority": "Medium", "steps": ["Verify the user's identity", "Reset the password", "Have the user log in and set a new password"]}

Ticket: Someone I don't know logged into my email
{"category": "Security", "priority": "High", "steps": ["Reset the user's password right away", "Sign out all active sessions", "Turn on two-factor authentication", "Report it to the security team"]}
"""


def get_api_key():
    # Streamlit Cloud keeps the key in "Secrets". On your Mac there is none, so Ollama is used.
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY")


def analyze(ticket):
    prompt = f"""You are an IT help desk assistant. Reply ONLY in JSON with keys: category, priority, steps.
- category: one of Account, Network, Hardware, Software, Security
- priority: High if many people are affected or there is a security risk. Medium if one person can't work. Low if they can still work.
- steps: a list of 3 to 5 troubleshooting steps. Never leave it empty.

{EXAMPLES}
Now classify this ticket.
Ticket: {ticket}"""
    api_key = get_api_key()
    if api_key:
        # Online: use Groq (free tier, no credit card)
        client = Groq(api_key=api_key)
        reply = client.chat.completions.create(model="openai/gpt-oss-20b", temperature=0,
                                               response_format={"type": "json_object"},
                                               messages=[{"role": "user", "content": prompt}])
        text = reply.choices[0].message.content
    else:
        # On your Mac: use Ollama
        reply = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}],
                            format="json", options={"temperature": 0})
        text = reply["message"]["content"]
    result = json.loads(text)
    steps = result.get("steps", [])
    if isinstance(steps, str):
        steps = [steps]
    result["steps"] = steps
    return result


# Idea 2: the ticket queue is saved in queue.csv
def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, newline="") as f:
        return list(csv.DictReader(f))


def save_queue(rows):
    with open(QUEUE_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# Idea 3: save the user's thumbs up / thumbs down
def set_feedback(ticket_id, value):
    rows = load_queue()
    for row in rows:
        if row["id"] == ticket_id:
            row["feedback"] = value
    save_queue(rows)


st.title("🛠️ Help Desk Ticket Assistant")
st.write("Describe the problem, and the AI will sort it and suggest fixes.")

ticket = st.text_area("Ticket", placeholder="Example: My laptop won't connect to Wi-Fi")

if st.button("Analyze") and ticket.strip():
    with st.spinner("Thinking..."):
        result = analyze(ticket)

    row = {
        "id": uuid.uuid4().hex[:8],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ticket": ticket.strip(),
        "category": result.get("category", "?"),
        "priority": result.get("priority", "?"),
        "steps": " | ".join(result["steps"]),
        "feedback": "",
    }
    rows = load_queue()
    rows.append(row)
    save_queue(rows)

    st.session_state.current = row
    st.session_state.steps = result["steps"]

# Show the latest result (stays on screen after clicking feedback buttons)
if "current" in st.session_state:
    row = st.session_state.current

    col1, col2 = st.columns(2)
    col1.metric("Category", row["category"])
    col2.metric("Priority", row["priority"])

    st.subheader("Suggested steps")
    for i, step in enumerate(st.session_state.steps, 1):
        st.write(f"{i}. {step}")

    st.write("**Was this answer right?**")
    good, bad = st.columns(2)
    if good.button("👍 Correct"):
        set_feedback(row["id"], "correct")
        st.success("Thanks! Marked as correct.")
    if bad.button("👎 Wrong"):
        set_feedback(row["id"], "wrong")
        st.warning("Thanks! Marked as wrong.")

# The queue
st.divider()
st.subheader("Ticket queue")
rows = load_queue()
if rows:
    rated = [r for r in rows if r["feedback"]]
    if rated:
        correct = sum(1 for r in rated if r["feedback"] == "correct")
        st.metric("AI accuracy (rated tickets)", f"{correct}/{len(rated)} correct")
    table = [{k: v for k, v in r.items() if k != "id"} for r in reversed(rows)]
    st.dataframe(table, hide_index=True)
else:
    st.write("No tickets yet.")
