import streamlit as st
import os
import io
import json
import base64
import requests
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Architect3D Studio | AI Floor Plan Visualizer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling (Dark-mode, Glassmorphism, Premium typography)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #21262d;
    }
    
    /* Force high contrast text colors inside the dark sidebar */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li {
        color: #c9d1d9 !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #58a6ff !important;
        font-weight: 700;
        margin-bottom: 0px;
    }
    
    /* Main Layout Styling */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Custom Headers */
    .title-gradient {
        background: linear-gradient(90deg, #58a6ff 0%, #bc8cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -0.05rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .subtitle {
        color: #8b949e;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Card/Glassmorphic Container */
    .glass-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    
    .glass-header {
        color: #58a6ff;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 1px solid #30363d;
        padding-bottom: 0.5rem;
    }
    
    /* Button Customization */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #8957e5 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.4);
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(137, 87, 229, 0.6);
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%); /* Green on hover indicating go */
    }
    
    div.stButton > button:first-child:active {
        transform: translateY(0);
    }

    /* Form Inputs styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }
    
    /* Alert details */
    .stAlert {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE SETUP -----------------
if "generated_image" not in st.session_state:
    st.session_state.generated_image = None
if "refined_prompt" not in st.session_state:
    st.session_state.refined_prompt = None
if "description" not in st.session_state:
    st.session_state.description = None
if "preview_images" not in st.session_state:
    st.session_state.preview_images = []

# ----------------- HELPER FUNCTIONS -----------------
def process_uploaded_file(uploaded_file):
    """
    Parses a single uploaded file (PDF or Image) and returns a list of PIL Images.
    Uses PyMuPDF (fitz) for PDF page extraction.
    """
    file_bytes = uploaded_file.read()
    file_ext = uploaded_file.name.split(".")[-1].lower()
    
    if file_ext == "pdf":
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            images = []
            # Extract first page (layout page)
            if doc.page_count > 0:
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                images.append(Image.open(io.BytesIO(img_data)))
            return images
        except Exception as e:
            st.error(f"Error parsing PDF '{uploaded_file.name}': {e}")
            return []
    else:
        try:
            return [Image.open(io.BytesIO(file_bytes))]
        except Exception as e:
            st.error(f"Error parsing image '{uploaded_file.name}': {e}")
            return []

def get_image_bytes(image):
    """Converts a PIL Image object to raw PNG bytes."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("# 🛠️ Configuration")
st.sidebar.markdown("---")

# Demo Mode Toggle
demo_mode = st.sidebar.checkbox(
    "Demo Mode (No API keys required)",
    value=False,
    help="Enable this to simulate the 3D rendering flow using pre-cached premium architectural mockups."
)

# API Provider Selection
api_provider = st.sidebar.selectbox(
    "AI Provider",
    ["Google Gemini", "OpenAI / OpenRouter"],
    help="Select the backend service to generate your 3D visualization."
)

# API Key Retrieval (Check environment variables as defaults)
default_gemini_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
default_openai_key = os.getenv("OPENAI_API_KEY") or ""

if api_provider == "Google Gemini":
    api_key = st.sidebar.text_input(
        "Gemini API Key",
        value=default_gemini_key,
        type="password",
        placeholder="AIzaSy..."
    )
else:
    api_key = st.sidebar.text_input(
        "OpenAI/OpenRouter API Key",
        value=default_openai_key,
        type="password",
        placeholder="sk-..."
    )
    
    # Advanced Settings for Custom Base URL
    with st.sidebar.expander("⚙️ Advanced API Settings"):
        default_base_url = "https://api.openai.com/v1"
        if api_key.startswith("sk-or-"):
            default_base_url = "https://openrouter.ai/api/v1"
        base_url = st.text_input(
            "API Base URL",
            value=default_base_url,
            help="Custom endpoint for OpenAI compatible services, e.g. OpenRouter."
        )
        
        openai_model = st.text_input(
            "OpenAI Chat Model",
            value="gpt-4o",
            help="The vision model used to analyze the 2D layout."
        )
        
        openai_image_model = st.text_input(
            "OpenAI Image Model",
            value="dall-e-3",
            help="The image generator model."
        )

# Property Configurations
st.sidebar.markdown("### 🏠 Property Parameters")
property_type = st.sidebar.radio(
    "Property Type",
    ["Villa", "Flat"],
    index=0
)

# Number of floors selection (Only active if Villa)
num_floors = 1
if property_type == "Villa":
    num_floors = st.sidebar.selectbox("Number of Floors", [1, 2, 3, 4], index=1)

dimension_choice = st.sidebar.selectbox(
    "Dimensions Preset",
    ["30x50 ft (1500 sq ft)", "40x60 ft (2400 sq ft)", "50x80 ft (4000 sq ft)", "Custom Size"]
)

if dimension_choice == "Custom Size":
    dimensions = st.sidebar.text_input("Enter Dimensions", value="25x50")
else:
    dimensions = dimension_choice

st.sidebar.markdown("---")
st.sidebar.markdown("🤖 **Architect3D** uses AI to interpret 2D floor plans and design realistic 3D volumetric representations.")

# ----------------- MAIN UI -----------------
st.markdown("<div class='title-gradient'>Architect3D Studio</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Transform 2D floor plans into photorealistic 3D architectural renders in seconds</div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("<div class='glass-card'><div class='glass-header'>📐 Upload 2D Blueprints</div>", unsafe_allow_html=True)
    
    uploaded_files_dict = {}
    if property_type == "Villa":
        st.markdown("##### Upload separate plans for each level:")
        floor_names = ["Ground Floor", "First Floor", "Second Floor", "Third Floor"]
        for i in range(num_floors):
            floor_name = floor_names[i]
            uploaded_files_dict[floor_name] = st.file_uploader(
                f"📤 {floor_name} Plan (PDF, PNG, JPG, JPEG)",
                type=["pdf", "png", "jpg", "jpeg"],
                key=f"upload_{floor_name.lower().replace(' ', '_')}"
            )
    else:
        uploaded_files_dict["Floor"] = st.file_uploader(
            "📤 Floor Plan (PDF, PNG, JPG, JPEG)",
            type=["pdf", "png", "jpg", "jpeg"],
            key="upload_single_floor"
        )
    
    # Process files
    parsed_images = []
    for floor_name, f in uploaded_files_dict.items():
        if f is not None:
            imgs = process_uploaded_file(f)
            if imgs:
                parsed_images.append((floor_name, imgs[0]))
                
    st.session_state.preview_images = parsed_images
    
    # Display image previews
    if len(st.session_state.preview_images) > 0:
        if len(st.session_state.preview_images) == 1:
            floor_name, img = st.session_state.preview_images[0]
            st.image(
                img, 
                caption=f"Uploaded {floor_name} Preview", 
                use_container_width=True
            )
        else:
            st.info(f"📁 {len(st.session_state.preview_images)} layout drawings loaded successfully.")
            tab_names = [floor_name for floor_name, _ in st.session_state.preview_images]
            tabs = st.tabs(tab_names)
            for idx, tab in enumerate(tabs):
                floor_name, img = st.session_state.preview_images[idx]
                with tab:
                    st.image(
                        img,
                        caption=f"{floor_name} Blueprint Preview",
                        use_container_width=True
                    )
    else:
        st.info("📂 Please upload 2D floor plan files or PDF documents to start.")
        
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass-card'><div class='glass-header'>🔮 3D Architectural Visual</div>", unsafe_allow_html=True)
    
    # Generate action button
    generate_btn = st.button("🚀 Generate 3D Render")
    
    # Handle AI Processing
    if generate_btn:
        if not demo_mode and not api_key:
            st.error("🔑 Please enter your API Key in the sidebar to proceed.")
        elif not st.session_state.preview_images:
            st.error("📐 Please upload at least one 2D floor plan file.")
        else:
            if demo_mode:
                import time
                with st.spinner("🔍 Step 1/2: Simulating 2D floor plan vision analysis..."):
                    time.sleep(1.5)
                    st.session_state.description = (
                        f"Simulated Analysis of the uploaded 2D {property_type} floor plan(s) at dimensions {dimensions}. "
                        "The layout structures show consistent room sizing, aligned doorways, and window frame positioning. "
                        "Volumetric parameters are validated."
                    )
                    st.session_state.refined_prompt = (
                        f"A photorealistic, highly detailed 3D architectural rendering of a modern {property_type.lower()}, "
                        f"dimensions {dimensions}. Featuring luxury styling, premium materials, warm lights, octane render, "
                        "architectural photography style."
                    )
                with st.spinner("🎨 Step 2/2: Rendering photorealistic 3D visualization (Simulated)..."):
                    time.sleep(1.5)
                    # Load from mock file
                    mock_filename = "mock_villa_render.png" if property_type == "Villa" else "mock_flat_render.png"
                    try:
                        with open(mock_filename, "rb") as f:
                            st.session_state.generated_image = f.read()
                        st.success("✨ 3D Render simulated successfully!")
                    except Exception as e:
                        st.error(f"Failed to load local mock image: {e}")
            else:
                # Construct vision prompt describing the upload layout structure
                floor_descriptions = []
                for idx, (floor_name, _) in enumerate(st.session_state.preview_images):
                    floor_descriptions.append(f"Image {idx+1} is the {floor_name} layout plan.")
                floor_info_str = "\n".join(floor_descriptions)
            
            vision_prompt = f"""
            You are an expert architectural designer. Analyze the attached 2D floor plan layout drawings.
            The user wants to visualize this property as a {property_type} with dimensions {dimensions}.
            There are {len(st.session_state.preview_images)} drawings uploaded:
            {floor_info_str}
            
            Analyze each floor plan in relation to the others. Describe the overall architectural structure, room distributions, wall alignments, door/window openings, and layout details in depth.
            Then, write a highly descriptive, detailed prompt for a high-quality 3D architectural rendering engine.
            The prompt should guide the image generator to create a photorealistic, stunning 3D architectural visualization of the exterior/interior or a 3D cutaway floor plan of the property.
            Include styles like: "modern architecture", "photorealistic", "luxurious design", "architectural photography", "octane render", "high-end finish".
            Ensure the prompt focuses on making the 3D visualization look premium and clean.
            
            Format your response as a JSON object with two keys:
            "description": "Your detailed analysis of the floor plan(s)",
            "rendering_prompt": "The detailed prompt for the image generator"
            """
            
            # ----------------- GOOGLE GEMINI FLOW -----------------
            if api_provider == "Google Gemini":
                try:
                    from google import genai
                    from google.genai import types
                    
                    with st.spinner(f"🔍 Step 1/2: Gemini analyzing the {len(st.session_state.preview_images)} 2D layout drawings..."):
                        client = genai.Client(api_key=api_key)
                        
                        # Pack all preview images as Parts for Gemini Multimodal input
                        contents = []
                        for _, img in st.session_state.preview_images:
                            img_bytes = get_image_bytes(img)
                            contents.append(
                                types.Part.from_bytes(
                                    data=img_bytes,
                                    mime_type="image/png"
                                )
                            )
                        # Append the text prompt
                        contents.append(vision_prompt)
                        
                        response = client.models.generate_content(
                            model='gemini-3.5-flash',
                            contents=contents,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        
                        # Parse JSON results
                        result_data = json.loads(response.text)
                        st.session_state.description = result_data.get("description", "")
                        st.session_state.refined_prompt = result_data.get("rendering_prompt", "")
                    
                    with st.spinner("🎨 Step 2/2: Imagen rendering the 3D visualization..."):
                        image_response = client.models.generate_content(
                            model='gemini-3.1-flash-image',
                            contents=st.session_state.refined_prompt,
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE"]
                            )
                        )
                        
                        generated_image_bytes = None
                        for part in image_response.candidates[0].content.parts:
                            if part.inline_data:
                                generated_image_bytes = part.inline_data.data
                                break
                                
                        if generated_image_bytes is None:
                            raise ValueError("No image data returned from the generation model.")
                            
                        st.session_state.generated_image = generated_image_bytes
                        st.success("✨ 3D Render generated successfully!")
                        
                except Exception as e:
                    st.error(f"❌ Gemini Generation failed: {e}")
                    st.info("Tip: Double-check your Gemini API key and ensure it has access to the standard Google GenAI models.")
            
            # ----------------- OPENAI FLOW -----------------
            else:
                try:
                    import openai
                    
                    with st.spinner(f"🔍 Step 1/2: GPT-4o analyzing the {len(st.session_state.preview_images)} 2D layout drawings..."):
                        # Build client
                        client = openai.OpenAI(api_key=api_key, base_url=base_url)
                        
                        content_parts = [{"type": "text", "text": vision_prompt}]
                        # Append all images as base64 blocks
                        for _, img in st.session_state.preview_images:
                            img_bytes = get_image_bytes(img)
                            base64_image = base64.b64encode(img_bytes).decode('utf-8')
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            })
                        
                        openai_messages = [
                            {
                                "role": "user",
                                "content": content_parts
                            }
                        ]
                        
                        response = client.chat.completions.create(
                            model=openai_model,
                            messages=openai_messages,
                            response_format={"type": "json_object"}
                        )
                        
                        result_data = json.loads(response.choices[0].message.content)
                        st.session_state.description = result_data.get("description", "")
                        st.session_state.refined_prompt = result_data.get("rendering_prompt", "")
                        
                    with st.spinner("🎨 Step 2/2: Generating image via DALL-E 3..."):
                        image_response = client.images.generate(
                            model=openai_image_model,
                            prompt=st.session_state.refined_prompt,
                            size="1024x1024",
                            quality="standard",
                            n=1
                        )
                        img_url = image_response.data[0].url
                        st.session_state.generated_image = requests.get(img_url).content
                        st.success("✨ 3D Render generated successfully!")
                        
                except Exception as e:
                    st.error(f"❌ OpenAI Generation failed: {e}")
                    st.info("Tip: Double-check your API Key, base URL, and model configurations.")

    # ----------------- DISPLAY GENERATED OUTPUT -----------------
    if st.session_state.generated_image is not None:
        # Show generated image
        st.image(
            st.session_state.generated_image, 
            caption=f"Generated 3D Visualization ({property_type})", 
            use_container_width=True
        )
        
        # Download button
        st.download_button(
            label="💾 Download 3D Render Image",
            data=st.session_state.generated_image,
            file_name=f"architect3d_{property_type.lower()}_render.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        # Placeholder styling
        st.markdown("""
        <div style="background-color: #161b22; border: 1.5px dashed #30363d; border-radius: 12px; height: 350px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
            <span style="font-size: 3rem; margin-bottom: 10px;">🏢</span>
            <p style="color: #8b949e; font-size: 1.1rem; font-weight: 500;">No render generated yet</p>
            <p style="color: #484f58; font-size: 0.9rem;">Set parameters and click 'Generate' to see magic happen</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- ANALYSIS DETAILS ACCORDION -----------------
if st.session_state.description is not None or st.session_state.refined_prompt is not None:
    st.markdown("---")
    with st.expander("👁️ View AI Architectural Analysis & Generation Prompt"):
        col_desc, col_prompt = st.columns(2)
        with col_desc:
            st.subheader("Layout Analysis")
            st.write(st.session_state.description)
        with col_prompt:
            st.subheader("Refined Rendering Prompt")
            st.info(st.session_state.refined_prompt)
