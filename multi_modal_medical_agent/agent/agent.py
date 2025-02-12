
import reflex as rx
from typing import Optional
import asyncio
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import os
from PIL import Image
import time
import asyncio

# Set Google API Key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class MedicalState(rx.State):
    """State for the medical imaging analysis application."""
    processing: bool = False
    upload_status: str = ""
    analysis_result: str = ""
    image_filename: str = ""
    _temp_image_path: str = ""

    query = """
            You are a highly skilled medical imaging expert with extensive knowledge in radiology and diagnostic imaging. Analyze the patient's medical image and structure your response as follows:

            ### 1. Image Type & Region
            - Specify imaging modality (X-ray/MRI/CT/Ultrasound/etc.)
            - Identify the patient's anatomical region and positioning
            - Comment on image quality and technical adequacy

            ### 2. Key Findings
            - List primary observations systematically
            - Note any abnormalities in the patient's imaging with precise descriptions
            - Include measurements and densities where relevant
            - Describe location, size, shape, and characteristics
            - Rate severity: Normal/Mild/Moderate/Severe

            ### 3. Diagnostic Assessment
            - Provide primary diagnosis with confidence level
            - List differential diagnoses in order of likelihood
            - Support each diagnosis with observed evidence from the patient's imaging
            - Note any critical or urgent findings

            ### 4. Patient-Friendly Explanation
            - Explain the findings in simple, clear language that the patient can understand
            - Avoid medical jargon or provide clear definitions
            - Include visual analogies if helpful
            - Address common patient concerns related to these findings

            ### 5. Research Context
            IMPORTANT: Use the DuckDuckGo search tool to:
            - Find recent medical literature about similar cases
            - Search for standard treatment protocols
            - Provide a list of relevant medical links of them too
            - Research any relevant technological advances
            - Include 2-3 key references to support your analysis

            Format your response using clear markdown headers and bullet points. Be concise yet thorough.
            """

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle medical image upload."""
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

            self.image_filename = filename
            self._temp_image_path = str(outfile)
            self.upload_status = "Image uploaded successfully!"
            
        except Exception as e:
            self.upload_status = f"Error uploading image: {str(e)}"

    @rx.var
    def medical_agent(self):
        if GOOGLE_API_KEY:
            return Agent(
                model=Gemini(
                    api_key=GOOGLE_API_KEY,
                    id="gemini-2.0-flash-exp"
                ),
                tools=[DuckDuckGo()],
                markdown=True
            )
        return None


    @rx.event(background=True)        
    async def analyze_image(self):
        """Process image using medical AI agent."""
        if not self.medical_agent:
            self.analysis_result = "API Key not configured in environment"
            return
            
        async with self:
            self.processing = True
            self.analysis_result = ""
            yield
            await asyncio.sleep(1)
            
        try:
            # Process image
            with Image.open(self._temp_image_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                new_width = 500
                new_height = int(new_width / aspect_ratio)
                resized_img = img.resize((new_width, new_height))
                resized_img.save(self._temp_image_path)

            # Run analysis
            result = self.medical_agent.run(self.query, images=[self._temp_image_path])
            
            async with self:
                self.analysis_result = result.content
                self.processing = False
            
        except Exception as e:
            async with self:
                self.processing = False
                self.analysis_result = f"An error occurred: {str(e)}"
        finally:
            if os.path.exists(self._temp_image_path):
                os.remove(self._temp_image_path)


def medical_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Medical Imaging Analysis Agent 🏥",
                class_name="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-600",
            ),
            rx.el.p(
                "Advanced AI-powered medical image analysis using Gemini 2.0 Flash",
                class_name="text-gray-600 mt-2 text-lg",
            ),
            class_name="text-center space-y-2",
        ),
        class_name="w-full py-8 bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-blue-100",
    )


def upload_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.upload(
                rx.el.div(
                    rx.el.div(
                        rx.el.i(class_name="fas fa-upload text-3xl text-blue-500 mb-4"),
                        rx.el.p(
                            "Drop your medical image here",
                            class_name="text-lg font-semibold text-gray-700 mb-2"
                        ),
                        rx.el.p(
                            "or click to browse",
                            class_name="text-sm text-gray-500"
                        ),
                        rx.el.p(
                            "Supported formats: JPG, PNG",
                            class_name="text-xs text-gray-400 mt-2"
                        ),
                        class_name="text-center",
                    ),
                    class_name="p-8 border-2 border-dashed border-blue-200 rounded-xl hover:border-blue-400 transition-colors duration-300",
                ),
                max_files=1,
                accept={".jpg", ".jpeg", ".png"},
                id="medical_upload",
                class_name="cursor-pointer",
            ),
            rx.cond(
                MedicalState.upload_status != "",
                rx.el.p(
                    MedicalState.upload_status,
                    class_name="mt-4 text-sm text-center text-blue-600",
                ),
            ),
            rx.el.button(
                "Upload Image",
                on_click=lambda: MedicalState.handle_upload(rx.upload_files(upload_id="medical_upload")),
                class_name="mt-4 w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all duration-300 shadow-md hover:shadow-lg",
            ),
            class_name="w-full max-w-md mx-auto",
        ),
        class_name="w-full bg-white p-6 rounded-xl shadow-md",
    )


def analysis_section() -> rx.Component:
    return rx.el.div(
        rx.cond(
            MedicalState.image_filename != "",
            rx.el.div(
                rx.el.div(
                    rx.el.img(
                        src=rx.get_upload_url(MedicalState.image_filename),
                        class_name="mx-auto my-4 max-w-2xl h-auto rounded-lg shadow-lg border border-gray-200",
                    ),
                    class_name="mb-6",
                ),
                rx.el.div(
                    rx.cond(
                        MedicalState.processing,
                        rx.el.div(
                            rx.el.div(
                                class_name="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"
                            ),
                            rx.el.p(
                                "Analyzing image...",
                                class_name="mt-2 text-sm text-gray-600"
                            ),
                            class_name="flex flex-col items-center justify-center p-4",
                        ),
                        rx.el.button(
                            "Analyze Image",
                            on_click=MedicalState.analyze_image,
                            diabled=MedicalState.processing,
                            class_name="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all duration-300 shadow-md hover:shadow-lg",
                        ),
                    ),
                ),
                rx.cond(
                    MedicalState.analysis_result != "",
                    rx.el.div(
                        rx.markdown(
                            MedicalState.analysis_result,
                            class_name="mt-4 p-4 bg-blue-50 text-blue-700 rounded-lg border border-blue-100",
                        ),
                    ),
                ),
                class_name="space-y-4",
            ),
        ),
        class_name="w-full bg-white p-6 rounded-xl shadow-md mt-6",
    )


def index() -> rx.Component:
    return rx.el.div(
        medical_header(),
        rx.el.div(
            rx.el.div(
                upload_section(),
                analysis_section(),
                class_name="max-w-4xl mx-auto px-4 space-y-6"
            ),
            class_name="py-8 bg-gray-50 min-h-screen"
        ),
        class_name="min-h-screen bg-gray-50"
    )


app = rx.App()
app.add_page(index)