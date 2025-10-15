# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the files**
```bash
cd /your/project/directory
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Test the underwriter**
```bash
python cre_underwriter.py
```
This will generate `cre_underwriting.xlsx` in the outputs folder.

4. **Start the API server**
```bash
python api.py
```
Server will start on `http://localhost:5000`

5. **Open the web interface**
```bash
# Open underwriting_interface.html in your browser
# Or use Python's built-in server:
python -m http.server 8000
# Then visit http://localhost:8000/underwriting_interface.html
```

6. **Test it out**
- Fill out the form with the pre-populated example data
- Click "Generate Underwriting Package"
- Excel file will download automatically
- Open it to see your professional underwriting analysis!

## 🌐 Deploy to Production

### Option 1: Heroku (Easiest)

1. **Create Heroku account** at heroku.com

2. **Install Heroku CLI**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

3. **Create app**
```bash
heroku create your-underwriting-app
```

4. **Create Procfile**
```bash
echo "web: python api.py" > Procfile
```

5. **Deploy**
```bash
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-underwriting-app
git push heroku main
```

6. **Open your app**
```bash
heroku open
```

**Cost:** Free tier for testing, $7/month for basic production

### Option 2: AWS EC2 (More Control)

1. **Launch EC2 instance** (t2.micro for free tier)

2. **SSH into instance**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

3. **Setup**
```bash
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
```

4. **Run with Gunicorn**
```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

5. **Setup Nginx** (optional, for HTTPS)
```bash
sudo apt install nginx
# Configure nginx as reverse proxy
```

**Cost:** Free tier eligible, ~$10-15/month after

### Option 3: Digital Ocean (Developer Friendly)

1. **Create droplet** at digitalocean.com ($5/month)

2. **One-click deploy:**
- Choose Ubuntu 22.04
- Select $5/month plan
- SSH and follow AWS EC2 steps above

### Option 4: Railway (Modern PaaS)

1. **Go to railway.app**

2. **Connect GitHub repo**

3. **Railway auto-detects Python**

4. **Deploy with one click**

**Cost:** $5/month for hobby tier

## 🔧 Configuration

Create `.env` file for configuration:

```env
# Server Config
PORT=5000
HOST=0.0.0.0
DEBUG=False

# Security
SECRET_KEY=your-secret-key-here

# File Storage (optional)
UPLOAD_FOLDER=/tmp/uploads
MAX_FILE_SIZE=10485760

# Rate Limiting (optional)
RATE_LIMIT=100 per hour

# Email (for sending reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database (for user accounts - future)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Load in `api.py`:
```python
from dotenv import load_dotenv
import os

load_dotenv()
PORT = int(os.getenv('PORT', 5000))
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Test the API directly:
```bash
# Health check
curl http://localhost:5000/health

# Generate underwriting
curl -X POST http://localhost:5000/underwrite/simple \
  -H "Content-Type: application/json" \
  -d @test_data.json \
  --output test_output.xlsx
```

## 📊 Monitoring

### Basic Logging
Add to `api.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log each request
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}")
```

### Error Tracking
Use Sentry (free tier):
```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

## 🔐 Security

### Add Authentication
```bash
pip install flask-jwt-extended
```

```python
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
    # Validate user credentials
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

@app.route('/underwrite', methods=['POST'])
@jwt_required()
def underwrite():
    # Protected endpoint
    pass
```

### Add CORS for Web Interface
```python
from flask_cors import CORS

CORS(app, resources={
    r"/underwrite/*": {
        "origins": ["https://your-frontend-domain.com"]
    }
})
```

## 📈 Scaling

### Add Redis Caching
```bash
pip install redis flask-caching
```

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@app.route('/underwrite/simple', methods=['POST'])
@cache.cached(timeout=300, key_prefix=lambda: request.get_json())
def underwrite_simple():
    # Cached for 5 minutes
    pass
```

### Add Queue for Async Processing
```bash
pip install celery redis
```

```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def generate_underwriting(data):
    # Process in background
    pass
```

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt --upgrade
```

### Excel file has formula errors
```bash
python /mnt/skills/public/xlsx/recalc.py output.xlsx
```

### API returns 500 error
Check logs:
```bash
tail -f /var/log/your-app/error.log
```

### Slow generation times
- Enable caching
- Optimize Excel formula generation
- Add more server instances

## 💡 Quick Wins

### Add Email Delivery
```python
from flask_mail import Mail, Message

mail = Mail(app)

def send_underwriting(email, file_path):
    msg = Message(
        "Your Underwriting Analysis",
        sender="noreply@your-app.com",
        recipients=[email]
    )
    with app.open_resource(file_path) as fp:
        msg.attach("underwriting.xlsx", "application/vnd.ms-excel", fp.read())
    mail.send(msg)
```

### Add User Accounts
```python
from flask_login import LoginManager, UserMixin, login_required

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
```

### Add Payment Processing
```bash
pip install stripe
```

```python
import stripe

stripe.api_key = 'your-stripe-secret-key'

@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    # Stripe integration
    pass
```

## 📚 Resources

- **Flask Documentation:** flask.palletsprojects.com
- **openpyxl Guide:** openpyxl.readthedocs.io
- **Deployment Guide:** realpython.com/flask-by-example-part-1-project-setup/
- **API Best Practices:** restfulapi.net

## 🎯 Next Steps

1. **Week 1:** Get basic deployment working
2. **Week 2:** Add user authentication
3. **Week 3:** Implement payment processing
4. **Week 4:** Launch beta to 10 brokers

## 💬 Need Help?

- Check the full README.md for detailed documentation
- Review API_DOCS.md for API specifications
- Email: support@your-startup.com
- Schedule demo: calendly.com/your-startup

---

**You're 5 minutes away from automating commercial real estate underwriting. Let's go! 🚀**
