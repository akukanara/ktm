import os

class Config:
    SECRET_KEY = "thisiskanaratunnel_secret"
    SQLALCHEMY_DATABASE_URI = "postgresql://kanara:akukanara@192.168.225.4/ktm"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # FRP Config
    FRPS_BIND_ADDR = "0.0.0.0"
    FRPS_BIND_PORT = 7000
    FRPS_GLOBAL_TOKEN = "thisiskanaratunnel"

    # Profile upload settings
    USE_S3_UPLOAD = False  # Set True to use S3, False to store locally
    PROFILE_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "data", "profile", "photos")

    # For S3 uploads
    S3_BUCKET = "your-bucket-name"
    S3_REGION = "ap-southeast-1"
    S3_KEY = "your-aws-access-key"
    S3_SECRET = "your-aws-secret-key"

    # Enable email verification
    ENABLE_EMAIL_VERIFICATION = True

    # Email SMTP config
    MAIL_SERVER = "smtp.zoho.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True  
    MAIL_USERNAME = "noreply@kanara.xyz"
    MAIL_PASSWORD = "&Rj63G$aL^!TK2"
    MAIL_DEFAULT_SENDER = ("Kana Tunnel", "noreply@kanara.xyz")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
