import reflex as rx
import google.generativeai as genai
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
import asyncio


class State(rx.State):
    """State for the multimodal AI agent application."""

    processing: bool = False
    upload_status: str = ""
    result: str = ""
    video_filename: str = ""
    video: str = ""
    question: str = ""

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle video file upload."""
        if not files:
            return

        try:
            file = files[0]
            upload_data = await file.read()

            filename = file.filename
            outfile = rx.get_upload_dir() / filename

            # Save the file
            with outfile.open("wb") as file_object:
                file_object.write(upload_data)

            self.video_filename = filename
            self.video = outfile
            self.upload_status = "Video uploaded successfully!"

        except Exception as e:
            self.upload_status = f"Error uploading video: {str(e)}"

    @rx.event(background=True)
    async def analyze_video(self):
        """Process video and answer question using AI agent."""
        if not self.question:
            async with self:
                self.result = "Please enter your question."
                return
        async with self:
            self.processing = True
            yield
            await asyncio.sleep(1)

        try:
            agent = Agent(
                name="Multimodal Video Analyst",
                model=Gemini(id="gemini-2.0-flash-exp"),
                tools=[DuckDuckGoTools()],
                markdown=True,
            )

            video_file = genai.upload_file(str(self.video))
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                # time.sleep(2)
                video_file = genai.get_file(video_file.name)

            prompt = f"""
            First analyze this video and then answer the following question using both
            the video analysis and web research: {self.question}
            Provide a comprehensive response focusing on practical, actionable information.
            """

            result = agent.run(prompt, videos=[video_file])

            async with self:
                self.result = result.content
                self.processing = False

        except Exception as e:
            async with self:
                self.processing = False
                self.result = f"An error occurred: {str(e)}"


color = "rgb(107,99,246)"


def index():
    return rx.container(
        rx.vstack(
            # Header section
            rx.heading("Multimodal AI Agent 🕵️‍♀️ 💬", size="8", mb="6"),
            # Upload section
            rx.vstack(
                rx.upload(
                    rx.vstack(
                        rx.button(
                            "Select a Video File",
                            color=color,
                            bg="white",
                            border=f"1px solid {color}",
                        ),
                        rx.text("Drag and drop or click to select"),
                    ),
                    accept={".mp4", ".mov", ".avi"},
                    max_files=1,
                    border="1px dashed",
                    padding="20px",
                    id="upload1",
                ),
                rx.cond(
                    rx.selected_files("upload1"),
                    rx.text(rx.selected_files("upload1")[0]),
                    rx.text(""),
                ),
                rx.button(
                    "Upload",
                    on_click=State.handle_upload(rx.upload_files(upload_id="upload1")),
                ),
                rx.text(State.upload_status),
                spacing="4",
            ),
            # Video and Analysis section
            rx.cond(
                State.video_filename != "",
                rx.vstack(
                    rx.video(
                        url=rx.get_upload_url(State.video_filename),
                        width="50%",
                        controls=True,
                    ),
                    rx.text_area(
                        placeholder="Ask any question related to the video - the AI Agent will analyze it and search the web if needed",
                        value=State.question,
                        on_change=State.set_question,
                        width="600px",
                        size="2",
                    ),
                    rx.button(
                        "Analyze & Research",
                        on_click=State.analyze_video,
                        loading=State.processing,
                    ),
                    rx.cond(
                        State.result != "",
                        rx.vstack(
                            rx.heading("🤖 Agent Response", size="4"),
                            rx.markdown(State.result),
                        ),
                    ),
                    width="100%",
                    spacing="4",
                ),
            ),
            width="100%",
            max_width="800px",
            spacing="6",
            padding="4",
        ),
        max_width="600px",
        margin="auto",
        padding="40px",
    )


app = rx.App()
app.add_page(index)
