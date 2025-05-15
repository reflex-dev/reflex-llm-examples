import reflex as rx
from langchain_ollama import ChatOllama
from browser_use import Agent
import asyncio


# Reflex App State
class State(rx.State):
    task_description: str = ""
    output: str = ""
    is_loading: bool = False

    @rx.event(background=True)
    async def execute_task(self):
        """Run the browser task using Ollama and update the output."""
        async with self:
            self.is_loading = True
            self.output = ""
            yield
            await asyncio.sleep(1)

        result = await self.run_search()
        async with self:
            self.output = result.final_result()
            self.is_loading = False
            yield

    async def run_search(self) -> str:
        try:
            agent = Agent(
                task=self.task_description,
                llm=ChatOllama(
                    model="qwen2.5:latest",
                    num_ctx=32000,  # Context length for the model
                ),
                max_actions_per_step=1,
            )
            result = await agent.run()
            return result
        except Exception as e:
            return f"Error: {str(e)}"


# Reflex UI
def index():
    return rx.container(
        rx.vstack(
            rx.heading("Open Source Operator using Browser Use 🔥", size="8"),
            rx.text("Enter your task description below:"),
            rx.text_area(
                placeholder="Task description...",
                value=State.task_description,
                on_change=State.set_task_description,
                width="100%",
                height="200px",
                resize="vertical",
            ),
            rx.button(
                "Run Task",
                on_click=State.execute_task,
                loading=State.is_loading,
                width="100%",
            ),
            rx.divider(),
            rx.cond(
                State.output != "",
                rx.box(
                    rx.text("Output:", font_weight="bold"),
                    rx.text(State.output, font_size="sm"),
                    border="1px solid #e2e8f0",
                    padding="1rem",
                    width="100%",
                    height="300px",
                    overflow_y="auto",
                    bg="gray.50",
                    rounded="md",
                ),
            ),
            spacing="4",
            align="center",
            width="100%",
            max_width="800px",
            padding="2rem",
        )
    )


# Run the Reflex App
app = rx.App()
app.add_page(index)
