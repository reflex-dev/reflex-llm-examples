# AI Medical Agent using Gemini 2.0 Flash

The **AI Medical Agent** leverages **Reflex**, **Agno**, and **Gemini 2.0 Flash** to provide detailed medical analysis on the provided images. It enables users to obtain comprehensive insights into medical conditions by analyzing images and simultaneously searching the web for additional information. The app generates detailed reports that assist in understanding possible diagnoses, conditions, and medical recommendations.

## Note

**Educational Purpose Only:** This project is intended for educational purposes only to demonstrate the power of AI in medical image analysis. It is **not** a substitute for professional medical advice, diagnosis, or treatment.

---

## Features

- **Medical Image Analysis:** Analyze images to detect potential medical conditions and provide insights based on AI-powered evaluation.
- **Symptom & Condition Insights:** Extract information related to possible conditions based on image analysis and web data retrieval.
- **Gemini 2.0 Flash Integration:** Utilizes Google's Gemini 2.0 Flash for fast, accurate, and dynamic responses.
- **Web Search & Data Aggregation:** Cross-checks image analysis results with trusted medical sources for enhanced accuracy.
- **Detailed Medical Reports:** Generates in-depth analysis, including professional insights, condition explanations, and potential next steps.

---

## Getting Started

### 1. Clone the Repository  
Clone the GitHub repository to your local machine:  
```bash  
git clone https://github.com/reflex-dev/reflex-llm-examples.git  
cd reflex-llm-examples/multi_modal_medical_agent
```  

### 2. Install Dependencies  
Install the required dependencies:  
```bash  
pip install -r requirements.txt  
```  

### 3. Set Up Gemini API Key  
To use the Gemini 2.0 Flash model, you need a **Google API Key**. Follow these steps:  
Go to [Google AI Studio](https://aistudio.google.com/apikey), get your API Key, and set it as an environment variable:  
   ```bash  
   export GOOGLE_API_KEY="your-api-key-here"  
   ```  

### 4. Run the Reflex App  
Start the application:  
```bash  
reflex run  
```  

---

## How It Works  

1. **Medical Image Upload:** Upload an image for analysis.
2. **Gemini 2.0 Flash Processing:** The app analyzes the image and cross-references web data to provide a detailed report.
3. **Condition Insights:** The report includes potential conditions, symptom explanations, and possible next steps.
4. **Trusted Sources:** The app retrieves data from verified medical sources to enhance accuracy.

---

## Why AI Medical Agent?

- **AI-Powered Medical Insights:** Provides advanced image analysis with AI to assist in medical understanding.
- **Real-Time Data Access:** Retrieves relevant medical information from trusted sources for enhanced accuracy.
- **User-Friendly:** Simple and intuitive experience, enabling easy image uploads and report generation.

---

## Contributing

We welcome contributions! Feel free to open issues or submit pull requests to improve the app.

---

