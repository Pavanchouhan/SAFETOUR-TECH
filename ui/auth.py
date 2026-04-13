import streamlit as st
import random
import time
import os
import smtplib
import json
import uuid
import hashlib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

OTP_EXPIRY = 300
SESSION_FILE = "logs/auth_session.json"
USERS_FILE = "logs/users.json"
SESSIONS_DIR = "logs/sessions"

def hash_password(password):
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password_strength(password):
    """Validate password strength. Returns (is_valid, error_message)."""
    # Common weak passwords
    weak_passwords = {
        'password', '123456', '12345678', 'qwerty', 'abc123', '111111',
        'password123', '123123', '1234567890', 'letmein', 'welcome',
        'monkey', 'dragon', 'master', 'sunshine', 'princess'
    }
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    if password.lower() in weak_passwords:
        return False, "Password too common. Use a stronger password"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numbers"
    
    return True, "Password is strong"

def load_users():
    """Load all registered users from storage."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to storage."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def user_exists(email):
    """Check if user already registered."""
    users = load_users()
    return email in users

def username_exists(username):
    """Check if username is already taken."""
    users = load_users()
    for user_data in users.values():
        if user_data.get('username', '').lower() == username.lower():
            return True
    return False

def register_user(email, username, password):
    """Register a new user with username and hashed password."""
    users = load_users()
    if email in users:
        return False, "Email already registered"
    if username_exists(username):
        return False, "Username already taken"
    users[email] = {
        'username': username,
        'password_hash': hash_password(password),
        'created_at': time.time()
    }
    save_users(users)
    return True, "User registered successfully"

def verify_login(email_or_username, password):
    """Verify email/username + password for login."""
    users = load_users()
    
    # Try to find user by email first
    user_email = None
    if email_or_username in users:
        user_email = email_or_username
    else:
        # Try to find by username
        for email, user_data in users.items():
            if user_data.get('username', '').lower() == email_or_username.lower():
                user_email = email
                break
    
    if not user_email:
        return False, "Email or username not registered"
    
    if users[user_email]['password_hash'] != hash_password(password):
        return False, "Incorrect password"
    
    return True, user_email

def create_session_token(email):
    """Create and store a session token for this user/device."""
    try:
        token = str(uuid.uuid4())
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        session_file = os.path.join(SESSIONS_DIR, f'{token}.json')
        with open(session_file, 'w') as f:
            json.dump({
                'email': email,
                'expires': int(time.time()) + 7*24*3600
            }, f)
        return token
    except Exception as e:
        print(f"Error creating session: {e}")
        return None

def restore_session_from_token(token):
    """Restore session from token stored in localStorage."""
    try:
        session_file = os.path.join(SESSIONS_DIR, f'{token}.json')
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                data = json.load(f)
            if data.get('expires', 0) > int(time.time()):
                return True, data.get('email')
    except:
        pass
    return False, None

# SMTP configuration (set these in your .env)
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)


def send_email_otp(to_email: str, otp: int) -> tuple[bool, str]:
    msg = EmailMessage()
    msg["Subject"] = "Your SAFETOUR OTP"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(f"Your SAFETOUR OTP is {otp}. Valid for 5 minutes.")

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True, "OTP sent"
    except Exception as e:
        return False, str(e)


def render_auth():
    st.sidebar.title("🔐 SafeTourTech Auth")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"  # "login" or "register"
    if "otp_data" not in st.session_state:
        st.session_state.otp_data = {}

    # Try to restore session from token in URL query param
    try:
        params = st.query_params
        if 'token' in params:
            token = params.get('token')[0]
            success, email = restore_session_from_token(token)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_email = email
            # Clear token from URL
            st.experimental_set_query_params()
    except Exception:
        pass

    # If logged in, show user info and logout
    if st.session_state.logged_in:
        st.sidebar.success(f"✅ Logged in as: {st.session_state.user_email}")
        if st.sidebar.button("🚪 Logout"):
            # Clear localStorage token on client
            st.components.v1.html("""
            <script>
            try { localStorage.removeItem('safetour_token'); } catch(e) {}
            </script>
            """, height=0)
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.otp_data = {}
            st.sidebar.success("Logged out successfully")
            st.rerun()
        return True

    # Show mode toggle (Login / Register)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔑 Login"):
            st.session_state.auth_mode = "login"
    with col2:
        if st.button("📝 Register"):
            st.session_state.auth_mode = "register"

    # REGISTRATION MODE
    if st.session_state.auth_mode == "register":
        st.sidebar.subheader("📝 Register New Account")
        reg_email = st.sidebar.text_input("Email", key="reg_email", placeholder="you@example.com")
        reg_username = st.sidebar.text_input("Username", key="reg_username", placeholder="choose_a_username")
        
        # Step 1: Send OTP
        if st.sidebar.button("Send OTP", key="send_otp_reg"):
            if not reg_email:
                st.sidebar.error("Please enter your email")
            elif not reg_username:
                st.sidebar.error("Please enter a username")
            elif user_exists(reg_email):
                st.sidebar.error("Email already registered. Please login instead.")
            elif username_exists(reg_username):
                st.sidebar.error("Username already taken. Please choose another.")
            elif not EMAIL_HOST or not EMAIL_USER or not EMAIL_PASS:
                st.sidebar.error("Email (SMTP) not configured")
            else:
                otp = random.randint(100000, 999999)
                st.session_state.otp_data = {
                    "otp": otp,
                    "time": int(time.time()),
                    "email": reg_email,
                    "username": reg_username,
                    "mode": "register"
                }
                ok, msg = send_email_otp(reg_email, otp)
                if ok:
                    st.sidebar.success("OTP sent to your email")
                else:
                    st.sidebar.error(f"Failed to send OTP: {msg}")

        # Step 2: Verify OTP
        if st.session_state.otp_data and st.session_state.otp_data.get("mode") == "register":
            user_otp = st.sidebar.text_input("Enter OTP", key="verify_otp_reg")
            if st.sidebar.button("Verify OTP", key="verify_btn_reg"):
                if int(time.time()) - st.session_state.otp_data.get("time", 0) > OTP_EXPIRY:
                    st.sidebar.error("OTP expired")
                    st.session_state.otp_data = {}
                elif user_otp == str(st.session_state.otp_data.get("otp")):
                    st.sidebar.success("OTP verified!")
                    # Move to password setup
                    st.session_state.otp_data["verified"] = True
                else:
                    st.sidebar.error("Invalid OTP")

        # Step 3: Set password
        if st.session_state.otp_data and st.session_state.otp_data.get("verified"):
            st.sidebar.write("**Set Your Password**")
            st.sidebar.caption("Must contain: uppercase, lowercase, numbers (min 6 chars)")
            password = st.sidebar.text_input("Password", type="password", key="reg_password")
            confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.sidebar.button("Create Account", key="create_account"):
                if not password:
                    st.sidebar.error("Please enter a password")
                elif password != confirm_password:
                    st.sidebar.error("Passwords do not match")
                else:
                    is_strong, error_msg = validate_password_strength(password)
                    if not is_strong:
                        st.sidebar.error(error_msg)
                    else:
                        otp_email = st.session_state.otp_data.get("email")
                        otp_username = st.session_state.otp_data.get("username")
                        ok, msg = register_user(otp_email, otp_username, password)
                        if ok:
                            st.sidebar.success("✅ Account created! Please login with your email/username and password.")
                            st.session_state.otp_data = {}
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.sidebar.error(f"Registration failed: {msg}")

    # LOGIN MODE
    else:
        st.sidebar.subheader("🔑 Login")
        login_input = st.sidebar.text_input("Email or Username", key="login_input", placeholder="you@example.com or username")
        login_password = st.sidebar.text_input("Password", type="password", key="login_password")
        
        if st.sidebar.button("Login", key="login_btn"):
            if not login_input or not login_password:
                st.sidebar.error("Please enter email/username and password")
            else:
                ok, user_email = verify_login(login_input, login_password)
                if ok:
                    # Create session token
                    token = create_session_token(user_email)
                    if token:
                        # Store token in localStorage
                        js = f"""
                        <script>
                        try {{ localStorage.setItem('safetour_token', '{token}'); }} catch(e) {{}}
                        </script>
                        """
                        st.components.v1.html(js, height=0)
                        st.session_state.logged_in = True
                        st.session_state.user_email = user_email
                        st.sidebar.success("✅ Login Successful")
                        st.rerun()
                    else:
                        st.sidebar.error("Session creation failed")
                else:
                    st.sidebar.error(user_email)

    return False
