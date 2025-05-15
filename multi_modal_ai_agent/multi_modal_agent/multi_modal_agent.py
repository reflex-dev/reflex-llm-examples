import reflex as rx
import google.generativeai as genai
import asyncio


class State(rx.State):
    """State for the multimodal AI agent application."""

    processing: bool = False
    upload_status: str = ""
    result: str = ""
    video_filename: str = ""
    video: str = ""
    question: str = ""

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle video file upload."""
        if not files:
            self.upload_status = "Please select a video file."
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
        """Process video and answer question using AI."""
        if not self.question:
            async with self:
                self.result = "Please enter your question."
                return

        if not self.video:
            async with self:
                self.result = "Please upload a video first."
                return

        async with self:
            self.processing = True
            self.result = "Analyzing Video..."
            yield
            await asyncio.sleep(1)

        try:
            client = genai.Client()

            video_file = client.files.upload(file=str(self.video))
            while video_file.state == "PROCESSING":
                await asyncio.sleep(2)
                # time.sleep(2)
                video_file = client.files.get(name=video_file.name)

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    video_file,
                    "Describe this video.",
                ],
            )

            async with self:
                self.result = response.text
                self.processing = False

        except Exception as e:
            async with self:
                self.processing = False
                self.result = f"An error occurred: {str(e)}"


def index() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            # Header section with gradient background
            rx.el.div(
                rx.el.h1(
                    "Multimodal AI Agent 🕵️‍♀️ 💬",
                    class_name="text-5xl font-bold text-white mb-4",
                ),
                class_name="w-full p-12 bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg shadow-lg mb-8 text-center",
            ),
            # Upload section
            rx.el.div(
                rx.upload(
                    rx.el.div(
                        rx.el.button(
                            "Select a Video File",
                            class_name="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition-colors",
                        ),
                        rx.el.p(
                            "Drag and drop or click to select",
                            class_name="text-gray-500 mt-2",
                        ),
                        class_name="text-center",
                    ),
                    accept={".mp4", ".mov", ".avi"},
                    max_files=1,
                    class_name="border-2 border-dashed border-gray-300 rounded-lg p-8 bg-gray-50 hover:bg-gray-100 transition-colors",
                    id="upload1",
                ),
                rx.cond(
                    rx.selected_files("upload1"),
                    rx.el.p(
                        rx.selected_files("upload1")[0], class_name="text-gray-600 mt-2"
                    ),
                    rx.el.p("", class_name="mt-2"),
                ),
                rx.el.button(
                    "Upload",
                    on_click=State.handle_upload(rx.upload_files(upload_id="upload1")),
                    class_name="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors mt-4",
                ),
                rx.el.p(State.upload_status, class_name="text-gray-600 mt-2"),
                class_name="mb-8 p-6 bg-white rounded-lg shadow-lg",
            ),
            # Video and Analysis section
            rx.cond(
                State.video_filename != "",
                rx.el.div(
                    rx.el.div(
                        rx.video(
                            url=rx.get_upload_url(State.video_filename),
                            controls=True,
                            class_name="w-full rounded-lg shadow-lg",
                        ),
                        class_name="mb-6",
                    ),
                    rx.el.textarea(
                        placeholder="Ask any question related to the video - the AI Agent will analyze it",
                        value=State.question,
                        on_change=State.set_question,
                        class_name="w-full p-4 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:ring-1 focus:ring-blue-600 h-32 resize-none",
                    ),
                    rx.el.button(
                        "Analyze & Research",
                        on_click=State.analyze_video,
                        loading=State.processing,
                        class_name="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors mt-4",
                    ),
                    rx.cond(
                        State.result != "",
                        rx.el.div(
                            rx.el.h2(
                                "🤖 Agent Response",
                                class_name="text-2xl font-bold text-gray-800 mb-4",
                            ),
                            rx.markdown(
                                State.result, class_name="prose prose-blue max-w-none"
                            ),
                            class_name="mt-8 p-6 bg-white rounded-lg shadow-lg",
                        ),
                    ),
                    class_name="space-y-6",
                ),
            ),
            class_name="max-w-3xl mx-auto px-4",
        ),
        class_name="min-h-screen bg-gray-50 py-12",
    )


app = rx.App()
app.add_page(index)
