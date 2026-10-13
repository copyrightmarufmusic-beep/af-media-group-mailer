import streamlit as st
import smtplib
import time
import re
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT = Path(__file__).parent
ASSETS = ROOT  # Images are stored in the repository root.

st.set_page_config(
    page_title="CRY DIGITAL MEDIA | Mail Operations",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { --cyan:#20e7ff; --blue:#247bff; --violet:#8b5cf6; --panel:rgba(12,22,43,.82); }
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: radial-gradient(ellipse at 10% 0%, #102a56 0%, #070b16 48%, #03050a 100%); color:#f4f8ff; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#080f20,#0b1426); border-right:1px solid rgba(32,231,255,.22); }
h1,h2,h3 { letter-spacing:-.035em; }
.hero { padding:24px 28px; border:1px solid rgba(32,231,255,.28); border-radius:22px;
background:linear-gradient(115deg,rgba(12,30,60,.94),rgba(16,13,43,.8)); box-shadow:0 15px 55px rgba(0,0,0,.22); animation:rise .65s ease-out both; }
.eyebrow { color:var(--cyan); font-size:12px; letter-spacing:.2em; font-weight:800; text-transform:uppercase; }
.hero-title { font-size:clamp(28px,4vw,46px); font-weight:800; line-height:1.08; margin:8px 0; }
.hero-sub { color:#a9bbd6; font-size:14px; }
.metric { background:var(--panel); border:1px solid rgba(130,165,220,.18); border-radius:17px; padding:18px 20px; min-height:112px; transition:transform .2s ease,border-color .2s ease; }
.metric:hover { transform:translateY(-3px); border-color:rgba(32,231,255,.55); }
.metric-label { color:#91a6c5; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; }
.metric-value { color:#f5f8ff; font-size:30px; font-weight:800; margin-top:8px; }
.panel { background:rgba(9,17,34,.72); border:1px solid rgba(130,165,220,.18); border-radius:18px; padding:20px; }
.stButton>button { background:linear-gradient(100deg,#087cf0,#00c7e8); color:#fff; font-weight:800; border:0; border-radius:12px; min-height:46px; transition:transform .18s ease,filter .18s ease; }
.stButton>button:hover { filter:brightness(1.12); transform:translateY(-1px); }
.stTextInput input,.stTextArea textarea,.stNumberInput input { background:rgba(2,8,20,.75)!important; color:#eef7ff!important; border-color:rgba(32,231,255,.3)!important; border-radius:10px!important; }
div[data-testid="stForm"] { background:rgba(9,17,34,.72); padding:20px; border:1px solid rgba(130,165,220,.18); border-radius:18px; }
hr { border-color:rgba(130,165,220,.18); }
@keyframes rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
@media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation:none!important; transition:none!important; } }
</style>
""", unsafe_allow_html=True)

def image_or_none(path):
    return str(path) if path.exists() else None

def parse_recipients(raw):
    candidates = re.split(r"[,;\n\s]+", raw.strip())
    result, seen = [], set()
    for item in candidates:
        if not item:
            continue
        item = item.strip()
        if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", item):
            raise ValueError(f"ইমেইল ঠিকানাটি সঠিক নয়: {item}")
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

if "sent_count" not in st.session_state:
    st.session_state.sent_count = 0
if "failed_count" not in st.session_state:
    st.session_state.failed_count = 0
if "last_run" not in st.session_state:
    st.session_state.last_run = "এখনও কোনো ব্যাচ চালানো হয়নি"
if "logs" not in st.session_state:
    st.session_state.logs = []

with st.sidebar:
    logo = image_or_none(ASSETS / "cry-digital-media-logo.png")
    if logo:
        st.image(logo, use_container_width=True)
    st.markdown("### SMTP কনফিগারেশন")
    st.caption("Credentials এই সেশনে ব্যবহার হবে; কোডে সংরক্ষণ করা হয় না।")
    email_user = st.text_input("প্রেরকের Gmail", placeholder="you@example.com")
    email_pass = st.text_input("Gmail App Password", type="password", help="Google App Password ব্যবহার করুন; আপনার মূল Gmail পাসওয়ার্ড নয়।")
    st.divider()
    delay = st.slider("প্রতি মেইলের বিরতি (সেকেন্ড)", min_value=5, max_value=60, value=5)
    st.caption("নিরাপত্তার জন্য প্রতি ব্যাচে সর্বোচ্চ ৫০ জন প্রাপক।")
    st.divider()
    ceo = image_or_none(ASSETS / "ceo-profile.png")
    if ceo:
        st.image(ceo, width=105)
    st.markdown("**MD Maruf**")
    st.caption("CEO / CRY DIGITAL MEDIA")

st.markdown("""
<div class="hero">
  <div class="eyebrow">CRY DIGITAL MEDIA · MAIL OPERATIONS</div>
  <div class="hero-title">High-Speed Mailer<br/>Control Center</div>
  <div class="hero-sub">A polished workspace for consent-based business communication, SMTP delivery and transparent reporting.</div>
</div>
""", unsafe_allow_html=True)

st.write("")
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f'<div class="metric"><div class="metric-label">Successful sends · session</div><div class="metric-value">{st.session_state.sent_count}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric"><div class="metric-label">Failed sends · session</div><div class="metric-value">{st.session_state.failed_count}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric"><div class="metric-label">Last batch</div><div class="metric-value" style="font-size:17px;padding-top:7px">{st.session_state.last_run}</div></div>', unsafe_allow_html=True)

st.write("")
st.markdown("### Compose a delivery batch")
st.caption("প্রাপকের তালিকায় কমা, সেমিকোলন, স্পেস বা নতুন লাইন দিয়ে একাধিক ইমেইল আলাদা করুন। শুধু অনুমতিপ্রাপ্ত/প্রাসঙ্গিক প্রাপকদের কাছে পাঠান।")

with st.form("mailer_form"):
    recipients_raw = st.text_area("প্রাপকের ইমেইল ঠিকানা", placeholder="partner@example.com\nteam@example.com", height=105)
    subject = st.text_input("ইমেইল সাবজেক্ট", placeholder="Business partnership inquiry")
    body = st.text_area("মেসেজ বডি", height=190, placeholder="আপনার মেসেজ লিখুন...")
    confirm = st.checkbox("আমি নিশ্চিত করছি, এই প্রাপকদের কাছে এই বার্তা পাঠানোর অনুমতি/বৈধ কারণ আমার আছে।")
    submitted = st.form_submit_button("✉️ Send batch", use_container_width=True)

if submitted:
    if not email_user.strip() or not email_pass.strip():
        st.error("প্রেরকের Gmail এবং Gmail App Password দিন।")
    elif not subject.strip() or not body.strip():
        st.error("সাবজেক্ট ও মেসেজ বডি পূরণ করুন।")
    elif not confirm:
        st.warning("পাঠানোর আগে প্রাপকদের অনুমতি/বৈধ কারণ নিশ্চিত করুন।")
    else:
        try:
            recipients = parse_recipients(recipients_raw)
            if not recipients:
                st.error("কমপক্ষে একটি প্রাপকের ইমেইল দিন।")
            elif len(recipients) > 50:
                st.error("একটি ব্যাচে সর্বোচ্চ ৫০টি অনন্য ইমেইল পাঠানো যাবে। তালিকাটি ভাগ করে পাঠান।")
            else:
                progress = st.progress(0, text="SMTP সংযোগ প্রস্তুত হচ্ছে…")
                status = st.empty()
                clean_pw = email_pass.replace(" ", "")
                success = 0
                failed = 0
                try:
                    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(email_user.strip(), clean_pw)
                        for idx, recipient in enumerate(recipients, start=1):
                            try:
                                msg = MIMEMultipart()
                                msg["From"] = email_user.strip()
                                msg["To"] = recipient
                                msg["Subject"] = subject.strip()
                                msg.attach(MIMEText(body, "plain", "utf-8"))
                                server.sendmail(email_user.strip(), [recipient], msg.as_string())
                                success += 1
                                st.session_state.sent_count += 1
                                log_status = "SUCCESS"
                            except Exception as exc:
                                failed += 1
                                st.session_state.failed_count += 1
                                log_status = f"FAILED — {str(exc)[:160]}"
                            st.session_state.logs.insert(0, {
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "recipient": recipient,
                                "status": log_status,
                            })
                            st.session_state.logs = st.session_state.logs[:100]
                            progress.progress(idx / len(recipients), text=f"প্রক্রিয়া চলছে: {idx}/{len(recipients)}")
                            status.info(f"সফল: {success} · ব্যর্থ: {failed} · বর্তমান: {recipient}")
                            if idx < len(recipients):
                                time.sleep(delay)
                    st.session_state.last_run = datetime.now().strftime("%H:%M:%S")
                    if failed:
                        st.warning(f"ব্যাচ শেষ। সফল: {success}, ব্যর্থ: {failed}। বিস্তারিত নিচে দেখুন।")
                    else:
                        st.success(f"ব্যাচ সম্পন্ন! {success}টি ইমেইল SMTP সার্ভারে গ্রহণের জন্য পাঠানো হয়েছে।")
                    st.rerun()
                except smtplib.SMTPAuthenticationError:
                    st.error("Gmail authentication ব্যর্থ। Gmail-এ 2-Step Verification চালু করে সঠিক App Password ব্যবহার করুন।")
                except Exception as exc:
                    st.error(f"SMTP সংযোগ/পাঠানোর সমস্যা: {exc}")
        except ValueError as exc:
            st.error(str(exc))

st.divider()
st.markdown("### Recent delivery activity")
if st.session_state.logs:
    st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
else:
    st.info("এই সেশনে এখনও কোনো delivery activity নেই।")

st.caption("Note: 'Successful' মানে SMTP সার্ভার বার্তাটি গ্রহণ করেছে—প্রাপকের ইনবক্সে পৌঁছানো নিশ্চিত নয়। এই ড্যাশবোর্ডের পরিসংখ্যান বর্তমান অ্যাপ সেশনে থাকে; স্থায়ী রিপোর্টিংয়ের জন্য ডাটাবেস সংযোগ প্রয়োজন।")
