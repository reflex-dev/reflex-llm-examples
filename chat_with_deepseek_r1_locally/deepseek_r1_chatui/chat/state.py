import os
import asyncio
from typing import AsyncGenerator, Optional
import reflex as rx
from ollama import AsyncClient
from langchain.prompts import PromptTemplate

ollama_client = AsyncClient()

class QA(rx.Base):
    """A question and answer pair."""
    question: str
    answer: str

DEFAULT_CHATS = {
    "Intros": [],
}

class State(rx.State):
    """The app state."""
    chats: dict[str, list[QA]] = DEFAULT_CHATS
    current_chat: str = "Intros"
    question: str = ""
    processing: bool = False
    new_chat_name: str = ""

    def create_chat(self):
        """Create a new chat."""
        if self.new_chat_name.strip():
            self.current_chat = self.new_chat_name
            self.chats[self.new_chat_name] = []
            self.new_chat_name = ""

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat."""
        self.current_chat = chat_name

    @rx.var(cache=True)
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles."""
        return list(self.chats.keys())

    def _get_chat_history(self) -> str:
        """Get formatted chat history for the current chat."""
        history = []
        for qa in self.chats[self.current_chat][:-1]:  # Exclude the current question
            history.extend([
                f"Human: {qa.question}",
                f"Assistant: {qa.answer}"
            ])
        return "\n".join(history)

    @rx.event(background=True)
    async def process_question(self, form_data: dict[str, str]) -> AsyncGenerator:
        """Process a question and get streaming response from Ollama."""
        # Get and validate question
        question = form_data.get("question", "").strip()
        if not question:
            return

        # Add the question to the list of questions
        async with self:
            qa = QA(question=question, answer="")
            self.chats[self.current_chat].append(qa)
            self.processing = True
            yield
            await asyncio.sleep(0.1)

        try:
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["chat_history", "question"],
                template="""You are a helpful AI assistant. Use the following chat history and question to provide a helpful response:

                Chat History:
                {chat_history}

                Current Question: {question}

                Please provide a detailed and helpful response."""
            )

            # Generate prompt with chat history
            prompt = prompt_template.format(
                chat_history=self._get_chat_history(),
                question=question
            )

            # Stream response from Ollama
            async for chunk in await ollama_client.chat(
                model='deepseek-r1:1.5b',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True,
            ):
                async with self:
                    if 'message' in chunk and 'content' in chunk['message']:
                        self.chats[self.current_chat][-1].answer += chunk['message']['content']
                        self.chats = self.chats
                        yield
                        await asyncio.sleep(0.05)  

        except Exception as e:
            async with self:
                self.chats[self.current_chat][-1].answer = f"Error: {str(e)}"
                self.chats = self.chats

        finally:
            async with self:
                self.processing = False
                yield