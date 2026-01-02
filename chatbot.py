import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["SUPABASE"]["OPENAI_API_KEY"])

def run_chatbot():
    st.subheader("🤖 Assistant Clinique")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Question clinique ou indicateurs")

    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Analyse..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Tu es un expert en qualité des soins, indicateurs hospitaliers "
                                "et sécurité des patients. Réponds en français."
                            )
                        }
                    ] + st.session_state.chat
                )
                answer = response.choices[0].message.content
                st.markdown(answer)

        st.session_state.chat.append({"role": "assistant", "content": answer})
