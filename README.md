# Architect3D Studio | AI Floor Plan Visualizer

Architect3D Studio is a Streamlit web application that takes 2D floor plans (PDFs or images) and leverages next-generation generative AI to construct stunning 3D architectural renders.

## 🚀 Setup & Local Execution

Follow these step-by-step instructions to create a virtual environment and run the application manually on your local system:

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed on your computer. You can check your version by running:
```bash
python --version
```

### 2. Create a Virtual Environment (`venv`)
Navigate to the project root directory in your terminal and execute:
```bash
python -m venv venv
```

### 3. Activate the Virtual Environment
Activate the environment based on your shell or command line tool:

* **PowerShell**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Note: If you get an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first).*
  
* **Command Prompt (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```

* **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
Once the virtual environment is active (indicated by `(venv)` in your prompt), upgrade `pip` and install the package requirements:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure API Keys
Create a file named `.env` in the root directory (one has been pre-configured for you locally) and add your keys:
```env
GOOGLE_AI_STUDIO_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 6. Run the App
Launch the Streamlit web server:
```bash
python -m streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🎨 Technology Stack
- **Frontend Framework**: Streamlit (Python)
- **AI Backend**:
  - Google Gemini API (`gemini-2.5-flash` for layout interpretation, `imagen-3.0-generate-002` for 3D mockup rendering)
  - OpenAI API (`gpt-4o` for layout interpretation, `dall-e-3` for 3D mockup rendering)
- **PDF Extraction**: PyMuPDF (`fitz`) - Pure python PDF parser (no Poppler required)
