import asyncio
import os

import google.generativeai as genai
import reflex as rx

key = os.getenv("KEY")
genai.configure(api_key=key)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 250,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat()


class State(rx.State):
    # ... unit of measurement
    units: dict[str, dict[str, str]] = {
        "metric": {"height": "cm", "weight": "kg", "age": "yrs"},
        "imperial": {"height": "ft", "weight": "lbs", "age": "yrs"},
    }
    selected_unit: str = "metric"
    # ... physical stats vars
    height: str
    weight: str
    age: str
    # ... form data
    data: dict[str, str]
    # ... user prompt
    prompt: str
    # ... chat history
    chat_history: list[dict[str, str]]
    # ... other chat vars
    is_generating: bool = False

    async def set_units(self, unit: str) -> None:
        self.selected_unit = unit

    async def set_profile_stats(self, info: list[str]) -> None:
        self.data["height"], self.data["weight"], self.data["age"] = (
            self.height + self.units[self.selected_unit]["height"],
            self.weight + self.units[self.selected_unit]["weight"],
            self.age + "years",
        )

        self.data[info[0]] = info[1]

    async def check_form_if_complete(self) -> bool:
        return len(self.data) == 8

    @rx.var
    def track_profil_stat_changes(self) -> dict[str, str]:
        if chat_session.history:
            chat_session.history.pop(0)

        chat_session.history.insert(
            0,
            {
                "role": "user",
                "parts": [
                    f"Take into account the following details when generating your answer {self.data}",
                ],
            },
        )

        return self.data

    async def send_prompt(self):
        if self.prompt:
            self.is_generating = True

            yield
            self.chat_history.append({"role": "user", "message": self.prompt})
            yield
            self.chat_history.append({"role": "gemini-1.5-flash", "message": ""})

            response = await self.send_message_to_chat(self.prompt)

            for word in response.split():
                for char in list(word):
                    self.chat_history[-1]["message"] += char
                    await asyncio.sleep(0.009)
                self.chat_history[-1]["message"] += " "
                yield

            self.prompt = ""
            self.is_generating = False

    async def send_message_to_chat(self, message):
        response = chat_session.send_message(message)
        return response.text
