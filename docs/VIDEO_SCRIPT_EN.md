# English presentation script — target: 4 minutes 20 seconds

Record the presentation only after the real LLM check succeeds. Speak the English text below. Show the indicated files and run the live demonstration; do not describe a local fallback as a Gemini response. Leave at least 30 seconds of buffer and finish before five minutes.

## 0:00–0:25 — Introduction

Hello, my name is Evelin Virguez. This is PicMe, my educational assistant for Universidad de Cundinamarca. It explains the MEDIT model and the Transhuman Person Declaration. My goal is to help students understand the principles, apply them to real situations, and check the sources.

## 0:25–1:10 — Architecture

This project has two interfaces: a Python desktop application and a web application. The desktop project also includes facial recognition. The educational chat is separate from that biometric database.

Here, the web page sends a question to the chat endpoint. The server retrieves relevant documents, prepares the context, and calls Gemini. The API key stays on the server. It is not included in the browser code or the public repository.

## 1:10–2:00 — Knowledge and prompting

The knowledge base contains thirty-two structured articles and six institutional sources. The desktop version stores this information in SQLite. The web version uses the same structured content.

This is lexical retrieval-augmented generation. The retriever selects up to four passages using weighted word matches and specific principle numbers. This implementation does not use embeddings.

The system prompt defines the educational purpose, restricts institutional facts to the retrieved evidence, and includes examples of expected behaviour. It also asks the model to distinguish official statements from educational examples. The output is structured JSON. The server checks that the cited article identifiers belong to the retrieved documents.

## 2:00–3:10 — Live demonstration

Now I will ask the assistant to compare principles five and nine in an educational situation.

Here is the response. The Gemini label confirms which mode produced it. I can open the source and check the explanation. The conversation also keeps a short context for follow-up questions.

Now I will ask a question outside the knowledge domain. The assistant recognises that the base does not support an answer. If the provider fails or the key is missing, it clearly identifies the local fallback. That fallback is not an LLM response.

## 3:10–4:00 — Ethical reflection

The declaration guides practical decisions in this project. Principles one and nine support autonomy: the assistant helps students think instead of replacing their judgement. Principles five and six support care and consideration for others, so the chat cannot access facial records. Principles seven and eleven require responsible improvement, rather than using technology simply because it is available.

Retrieval and citation checks can reduce errors, but they cannot guarantee that every generated claim is correct. Human review remains necessary.

## 4:00–4:25 — Delivery and conclusion

The repository includes the installation instructions, tests, architecture, system prompt, and the reflection in Spanish and English. This is the deployed application, and this is the public GitHub repository.

PicMe shows how technology can support educational transformation while responsibility remains human. Thank you.

---

For the final sentence about GitHub and deployment, show verified, accessible links. If they are not ready, complete that step before recording the final submission.
