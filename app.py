from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

app=FastAPI(debug=True)

#Mount the static files
app.mount("/static",StaticFiles(directory=r"./static"),name="static")

#Set up templates directory.
templates=Jinja2Templates(directory=r"./templates")

@app.get("/")
def get(request:Request):
    return templates.TemplateResponse('dashboard.html', {'request': request})
