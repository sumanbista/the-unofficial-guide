"""Gradio query interface (Milestone 5).

Run:  python app.py   →  http://localhost:7860

A question box drives the end-to-end ask() from query.py and shows the grounded
answer plus the documents it was retrieved from. The example questions at the
top are clickable: clicking one fills the box and answers immediately.
"""

import gradio as gr

from query import ask


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


# The five Evaluation Plan questions from planning.md.
EXAMPLES = [
    "What is John DeNero's overall quality rating?",
    "What classes does Professor Jennifer Listgarten teach?",
    "Do students need prior programming experience to succeed in UC Berkeley's CS program?",
    'What is the "Would Take Again" percentage for Professor Kannan Ramchandran?',
    "What do students say about Professor Satish Rao's teaching?",
]

with gr.Blocks(title="The Unofficial Guide — UC Berkeley CS") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about UC Berkeley CS/EECS courses and professors. Answers are "
        "grounded in real student reviews and Reddit/Medium threads — if the "
        "corpus doesn't cover it, the system says so instead of guessing."
    )

    inp = gr.Textbox(label="Your question", placeholder="e.g. Is CS70 hard?")

    gr.Markdown("**Try an example:**")
    with gr.Row():
        example_btns = [gr.Button(q, size="sm") for q in EXAMPLES]

    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    # Wire handlers after every component exists.
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    # Clicking an example fills the box AND answers in one click (no Ask needed).
    for b, q in zip(example_btns, EXAMPLES):
        b.click(
            lambda q=q: (q, *handle_query(q)),
            outputs=[inp, answer, sources],
        )


if __name__ == "__main__":
    demo.launch()
