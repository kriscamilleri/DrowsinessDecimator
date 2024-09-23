## Setup
1. **Create the virtual environment:**

   ```
   python3 -m venv .venv
   ```

2. **Activate the virtual environment:**

   - **Windows:**
     ```
     .venv\Scripts\activate
     ```

   - **macOS/Linux:**
     ```
     source .venv/bin/activate
     ```

3. **Install Dependencies:**

   Place the `requirements.txt` file in your project directory and run:

   ```
   pip install --upgrade pip  # Upgrade pip to the latest version
   pip install -r requirements.txt
   ```

## Build
   - **macOS/Linux:**
    ```
    pyinstaller main.py --name DrowsinessDetector --onefile \
    --add-data "$(python -c 'import mediapipe as mp; print(mp.__path__[0])')/modules:mediapipe/modules" \
    --hidden-import "mediapipe.python.solutions.face_mesh_connections" \
    --hidden-import "mediapipe.python.solutions.drawing_utils" \
    --hidden-import "mediapipe.python.solutions.face_mesh"
    ```
