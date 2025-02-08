from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import zipfile
import os

UPLOAD_DIR = "./uploaded_files"
UNZIP_DIR = "./unzipped_files"

app=FastAPI(debug=True)

#Mount the static files
app.mount("/static",StaticFiles(directory=r"./static"),name="static")

#Set up templates directory.
templates=Jinja2Templates(directory=r"./templates")

@app.get("/")
def get(request:Request):
    return templates.TemplateResponse('dashboard.html', {'request': request})

@app.get("/add-module")
def add_module(request:Request):
    return templates.TemplateResponse('add-module.html', {'request': request})

@app.post("/add-module")
async def add_module(module_name: str = Form(...), file: UploadFile = File(...)):
    # Ensure the uploaded file is a ZIP file
    if file.content_type != "application/zip":
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed.")

    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Unzip the file
    unzip_path = os.path.join(UNZIP_DIR, module_name)
    os.makedirs(unzip_path, exist_ok=True)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_path)
            file_list = zip_ref.namelist()  # Get the list of files in the zip

        # Print the names of the uncompressed files
        print(f"Extracted files for module '{module_name}':")
        for file_name in file_list:
            print(file_name)

        return JSONResponse(content={
            "message": "Module uploaded and unzipped successfully",
            "module_name": module_name,
            "extracted_files": file_list
        })
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")