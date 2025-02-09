import os
import zipfile
import sqlite3
from datetime import datetime
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse,JSONResponse

UPLOAD_DIR = "./uploaded_files"
UNZIP_DIR = "./unzipped_files"
DB_FILE = "./modules.db"

app = FastAPI(debug=True)

# Mount static files
app.mount("/static", StaticFiles(directory=r"./static"), name="static")

# Set up templates directory
templates = Jinja2Templates(directory=r"./templates")

# DB initialization
def initialize_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(UNZIP_DIR, exist_ok=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL,
                uploaded_time TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                extracted_files TEXT
            )
        ''')
        conn.commit()

initialize_db()

@app.get("/")
def get(request: Request):
    # Fetch module data from the database
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT module_name, uploaded_time, filename, file_size, extracted_files 
            FROM modules
        ''')
        rows = cursor.fetchall()

    # Transform the result into a list of dictionaries
    modules = [
        {
            "module_name": row[0],
            "uploaded_time": row[1],
            "filename": row[2],
            "file_size": row[3],
            "extracted_files": row[4].split(", ") if row[4] else []
        }
        for row in rows
    ]

    # Pass module data to the template
    return templates.TemplateResponse('dashboard.html', {'request': request, 'modules': modules})

@app.get("/add-module")
def add_module(request: Request):
    return templates.TemplateResponse('add-module.html', {'request': request})

@app.get("/module-mng")
def add_manage(request:Request):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, module_name, uploaded_time, filename, file_size, extracted_files
            FROM modules
        ''')
        rows = cursor.fetchall()

        # Structure the response
        modules = [
            {
                "id": row[0],
                "module_name": row[1],
                "uploaded_time": row[2],
                "filename": row[3],
                "file_size": row[4],
                "extracted_files": row[5].split(", ") if row[5] else []
            }
            for row in rows
        ]

    return templates.TemplateResponse('module-tables.html', {'request': request, 'modules': modules})

#Endpoint to delete a specific module.
@app.delete("/delete-module/{module_id}")
def delete_module(module_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM modules WHERE id = ?", (module_id,))
        conn.commit()
    return JSONResponse(content={"message": f"Module with ID {module_id} deleted."})

@app.get("/modules")
def get_all_modules():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, module_name, uploaded_time, filename, file_size, extracted_files
            FROM modules
        ''')
        rows = cursor.fetchall()

        # Structure the response
        modules = [
            {
                "id": row[0],
                "module_name": row[1],
                "uploaded_time": row[2],
                "filename": row[3],
                "file_size": row[4],
                "extracted_files": row[5].split(", ") if row[5] else []
            }
            for row in rows
        ]

    return JSONResponse(content={"modules": modules})

@app.post("/add-module")
async def add_module(module_name: str = Form(...), file: UploadFile = File(...)):
    # Ensure the uploaded file is a ZIP file
    if file.content_type != "application/zip":
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed.")

    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Get file size
    file_size = os.path.getsize(file_path)

    # Unzip the file
    unzip_path = os.path.join(UNZIP_DIR, module_name)
    os.makedirs(unzip_path, exist_ok=True)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_path)
            file_list = zip_ref.namelist()  # Get the list of files in the zip

        # Save module info in the database
        uploaded_time = datetime.now().isoformat()
        extracted_files_str = ", ".join(file_list)

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO modules (module_name, uploaded_time, filename, file_size, extracted_files)
                VALUES (?, ?, ?, ?, ?)
            ''', (module_name, uploaded_time, file.filename, file_size, extracted_files_str))
            conn.commit()

        print(f"Extracted files for module '{module_name}': {file_list}")
        return RedirectResponse(url="/", status_code=303)

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")
