import ollama, json, csv

with open("tickets.txt") as f:
    tickets = [line.strip() for line in f if line.strip()]

with open("results.csv", "w", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["ticket", "category", "priority", "steps"])

    for ticket in tickets:
        prompt = f"""You are an IT help desk assistant. Reply ONLY in JSON with keys: category, priority, steps.
- category: one of Account, Network, Hardware, Software, Security
- priority: High if many people are affected or there is a security risk. Medium if one person can't work. Low if they can still work.
- steps: a list of 3 to 5 troubleshooting steps. Never leave it empty.
Ticket: {ticket}"""

        reply = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}], format="json", options={"temperature": 0})
        result = json.loads(reply["message"]["content"])

        steps = result.get("steps", [])
        if isinstance(steps, list):
            steps = " | ".join(steps)

        writer.writerow([ticket, result.get("category"), result.get("priority"), steps])
        print(ticket, "->", result.get("category"), result.get("priority"))

print("\nDone! Results saved to results.csv")
