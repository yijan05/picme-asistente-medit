# Video in English - target: 4 minutes 40 seconds

Speak the English paragraphs below. The notes in italics indicate what to show and are not part of the narration. Practise with a timer and finish within five minutes. Check the real Gemini connection and the deployed link before recording.

## 0:00-0:20 - Introduction

Hello, my name is Evelin Yijan Virguez Parra. This is PicMe, my project for Universidad de Cundinamarca. I integrated an assistant that explains MEDIT and the Transhuman Person Declaration. The desktop assistant also answers questions about registration and entry records.

## 0:20-1:10 - Architecture and API

*Show desktop/app/chatbot/rag.py, desktop/app/chatbot/picme_queries.py and app/api/chat/route.ts.*

The project has a Python desktop application and a web interface. Educational questions follow a retrieval and generation process: the application finds relevant documents, builds the context and sends it to Gemini.

Operational questions follow a different route. The desktop application uses predefined, read-only SQLite queries. It does not ask Gemini to create SQL or change student records. Personal history requires a signed-in account, and access to another person's history requires authorization.

The Gemini API key is stored in local configuration or in the hosting environment. It is excluded from the public source code.

## 1:10-2:00 - Knowledge and prompt

*Show desktop/conocimiento/base_conocimiento.json, system_prompt.txt and desktop/app/chatbot/llm.py.*

The knowledge base contains thirty-three articles and six institutional sources. The desktop uses SQLite, and the web uses structured JSON.

The system retrieves up to four articles using weighted word matches and principle numbers. This is lexical retrieval-augmented generation. It does not use embeddings.

The system prompt limits institutional claims to the retrieved evidence. It includes examples, preserves the meaning of the declaration and separates official statements from educational interpretations. Gemini returns structured JSON. The application checks the format and the article references before displaying the answer and its sources.

## 2:00-3:15 - Live demonstration

*Open the deployed chatbot. Ask "Explain principle 6". Wait for a real Gemini response and show its source. Then open the desktop chatbot and ask "How many people are registered in PicMe?".*

First, I will ask the web assistant to explain principle six.

This response is labelled Gemini, and the source is available for verification. The declaration encourages us to consider other people, living beings and nature.

Now, I will ask the desktop assistant how many people are registered in PicMe.

This answer is labelled SQLite because it comes from the local database. The result is not sent to Gemini. These two examples show the difference between an educational LLM response and an operational database query.

## 3:15-4:15 - Ethical reflection

*Show the reflection sections in Spanish and English in the README.*

The declaration guides the design. Principles one and nine support autonomy: students remain responsible for their decisions. Principles five and six support care and consideration for others. The assistant does not read facial templates or passwords.

Principles seven and eleven encourage responsible improvement. Technology can support learning, but it does not replace human judgement.

For example, when a user asks whether they are a transhuman person, the assistant offers an educational reflection. It does not assign an identity or issue a certificate.

The sources and validation checks help users review the answers, but they cannot guarantee that every statement is correct.

## 4:15-4:40 - Delivery

*Show the public repository and the working deployment address.*

The public repository contains the source code, installation instructions, tests and the reflection in both languages. This is the working cloud application.

PicMe connects educational support with a practical project while keeping responsibility and personal reflection with the user. Thank you.

---

If Gemini falls back to a local answer, resolve the connection and record the demonstration again. The presence of a configured key alone does not demonstrate a real LLM response. The desktop and web checks must match the version shown in the video.
