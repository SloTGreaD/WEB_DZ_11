from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = 'your_cloud_name',
    api_key = 'your_api_key',
    api_secret = 'your_api_secret'
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/create_contact")
@limiter.limit("5/minute")
async def create_contact():
    return {"message": "Contact created successfully"}


origins = [
    "http://localhost:3000",  
    "https://Mywebsite.com",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


@app.post("/upload_avatar")
async def upload_avatar(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        return {"error": "File is not an image."}
    upload_result = cloudinary.uploader.upload(file.file, folder="avatars")
    return {"avatar_url": upload_result['url']}