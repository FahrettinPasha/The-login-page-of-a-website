from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import random
import string
from datetime import datetime, timedelta, date
import os
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import re
import requests # reCAPTCHA doğrulaması için eklendi

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cok_gizli_bir_anahtar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'karacemalopsiyonel@gmail.com'  # Your GMAIL address
app.config['MAIL_PASSWORD'] = 'yjvf wjii iofc jnwo'      # Your Google App Password

# reCAPTCHA Secret Key (BURAYI KENDİ ANAHTARINLA DEĞİŞTİR!)
app.config['RECAPTCHA_SECRET_KEY'] = 'YOUR_RECAPTCHA_SECRET_KEY' 

mail = Mail(app)
db = SQLAlchemy(app)

# Tokenizer object for password reset links
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# User Model - CİNSİYET SÜTUNU EKLENDİ
class Kullanici(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    sifre = db.Column(db.String(255), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    tc_no = db.Column(db.String(11), nullable=False)
    adres = db.Column(db.Text)
    dogum_tarihi = db.Column(db.Date, nullable=False)
    dogrulandi_mi = db.Column(db.Boolean, default=False)
    dogrulama_kodu = db.Column(db.String(6))
    kod_zaman = db.Column(db.DateTime)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    rol = db.Column(db.String(20), nullable=False, default='normal') # 'normal' veya 'sürücü'
    cinsiyet = db.Column(db.String(10), nullable=False) # 'erkek', 'kadın', 'diğer'

# Generate a random 6-digit code
def rastgele_kod():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Check password strength
def check_password_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"[0-9]", password):
        score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1

    if score < 3:
        return "Şifreniz çok zayıf. En az 3 farklı kriteri (minimum 8 karakter, büyük harf, küçük harf, rakam, özel karakter) karşılamalısınız."
    
    return None

# Function to send verification email
def send_verification_email(user_email, verification_code):
    msg = Message("Kargo Takip Sistemi - Doğrulama Kodunuz",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user_email])
    msg.body = f"Kayıt işleminizi tamamlamak için doğrulama kodunuz: {verification_code}\n\nBu kodu 10 dakika içinde kullanmanız gerekmektedir."
    try:
        mail.send(msg)
        print(f"Doğrulama kodu {user_email} adresine gönderildi.")
    except Exception as e:
        print(f"E-posta gönderme hatası: {e}")
        flash(f"Doğrulama e-postası gönderilemedi: Sunucu hatası veya internet bağlantısı sorunu. Lütfen daha sonra tekrar deneyin.", 'error')

# Function to send password reset email
def send_password_reset_email(user_email, token):
    reset_link = url_for('reset_password_token', token=token, _external=True)
    msg = Message("Kargo Takip Sistemi - Şifre Sıfırlama Talebi",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user_email])
    msg.body = f"Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n\n{reset_link}\n\nBu bağlantı 1 saat içinde geçerliliğini yitirecektir."
    try:
        mail.send(msg)
        print(f"Şifre sıfırlama linki {user_email} adresine gönderildi.")
    except Exception as e:
        print(f"E-posta gönderme hatası: {e}")
        flash(f"Şifre sıfırlama e-postası gönderilemedi: Sunucu hatası veya internet bağlantısı sorunu. Lütfen daha sonra tekrar deneyin.", 'error')

# Home Page (Registration Form)
@app.route('/')
def index():
    # form_data'ya varsayılan rolü ve boş cinsiyeti ekle
    return render_template('register.html', form_data={'rol': 'normal', 'cinsiyet': ''}) 

# Registration Process - CİNSİYET BİLGİSİ ALINDI VE KONTROL EDİLDİ
@app.route('/kayit', methods=['POST'])
def kayit():
    veri = request.form
    ad = veri.get('ad', '').strip()
    soyad = veri.get('soyad', '').strip()
    username = veri.get('username', '').strip().lower()
    email = veri.get('email', '').strip().lower()
    sifre = veri.get('sifre', '')
    confirm_sifre = veri.get('confirm_sifre', '')
    telefon = veri.get('telefon', '').strip()
    tc_no = veri.get('tc_no', '').strip()
    adres = veri.get('adres', '').strip()
    dogum_tarihi_str = veri.get('dogum_tarihi', '').strip()
    rol = veri.get('rol', 'normal').strip().lower()
    cinsiyet = veri.get('cinsiyet', '').strip().lower() # Cinsiyet bilgisini al
    recaptcha_response = veri.get('g-recaptcha-response')

    # Store form data to pass back to template in case of error (password excluded)
    form_data = {
        'ad': ad,
        'soyad': soyad,
        'username': username,
        'email': email,
        'telefon': telefon,
        'tc_no': tc_no,
        'adres': adres,
        'dogum_tarihi': dogum_tarihi_str,
        'rol': rol,
        'cinsiyet': cinsiyet # Cinsiyet bilgisini de form_data'ya ekle
    }

    # Rol kontrolü
    if rol not in ['normal', 'sürücü']:
        flash('Geçersiz kullanıcı rolü seçimi.', 'error')
        return render_template('register.html', form_data=form_data)

    # Cinsiyet kontrolü - SADECE 'erkek' ve 'kadın' kabul edildi
    if cinsiyet not in ['erkek', 'kadın']:
        flash('Lütfen geçerli bir cinsiyet seçimi yapın (Erkek veya Kadın).', 'error')
        return render_template('register.html', form_data=form_data)

    # reCAPTCHA doğrulaması
    if not recaptcha_response:
        flash('Lütfen reCAPTCHA doğrulamasını tamamlayın.', 'error')
        return render_template('register.html', form_data=form_data)
    
    recaptcha_verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    recaptcha_payload = {
        'secret': app.config['RECAPTCHA_SECRET_KEY'],
        'response': recaptcha_response,
        'remoteip': request.remote_addr
    }
    
    try:
        recaptcha_request = requests.post(recaptcha_verify_url, data=recaptcha_payload)
        recaptcha_result = recaptcha_request.json()
        if not recaptcha_result.get('success'):
            flash('reCAPTCHA doğrulaması başarısız oldu. Lütfen tekrar deneyin.', 'error')
            return render_template('register.html', form_data=form_data)
    except requests.exceptions.RequestException as e:
        flash(f'reCAPTCHA doğrulaması sırasında bir hata oluştu: {e}', 'error')
        return render_template('register.html', form_data=form_data)


    # Server-side validation (existing checks)
    if not ad or not soyad:
        flash('Ad ve Soyad boş bırakılamaz.', 'error')
        return render_template('register.html', form_data=form_data)
    if not username:
        flash('Kullanıcı adı boş bırakılamaz.', 'error')
        return render_template('register.html', form_data=form_data)
    if not email or '@' not in email or '.' not in email:
        flash('Geçerli bir e-posta adresi giriniz.', 'error')
        return render_template('register.html', form_data=form_data)
    
    # Şifrelerin eşleşme kontrolü
    if sifre != confirm_sifre:
        flash('Şifreler eşleşmiyor!', 'error')
        return render_template('register.html', form_data=form_data)

    # Password strength check
    password_strength_error = check_password_strength(sifre)
    if password_strength_error:
        flash(password_strength_error, 'error')
        return render_template('register.html', form_data=form_data)

    # Phone number validation
    clean_telefon = telefon.replace('+', '')
    if not clean_telefon.isdigit() or not (10 <= len(clean_telefon) <= 15):
        flash('Geçerli bir telefon numarası giriniz (sadece rakamlar, 10-15 hane arası).', 'error')
        return render_template('register.html', form_data=form_data)

    # TC ID number validation
    if not tc_no or not tc_no.isdigit() or len(tc_no) != 11:
        flash('TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır.', 'error')
        return render_template('register.html', form_data=form_data)
    
    # Birth date validation
    try:
        dogum_tarihi = datetime.strptime(dogum_tarihi_str, '%Y-%m-%d').date()
        if dogum_tarihi > datetime.now().date():
            flash('Doğum tarihi gelecekte olamaz.', 'error')
            return render_template('register.html', form_data=form_data)

        today = date.today()
        eighteen_years_ago = today.replace(year=today.year - 18)
        if dogum_tarihi > eighteen_years_ago:
            flash('Kayıt olmak için en az 18 yaşında olmalısınız.', 'error')
            return render_template('register.html', form_data=form_data)

    except ValueError:
        flash('Geçerli bir doğum tarihi giriniz.', 'error')
        return render_template('register.html', form_data=form_data)

    # Check if email or username already exists, and if unverified, redirect to verification
    existing_user_by_email = Kullanici.query.filter_by(email=email).first()
    existing_user_by_username = Kullanici.query.filter_by(username=username).first()

    if existing_user_by_email:
        if not existing_user_by_email.dogrulandi_mi:
            # User exists but not verified, resend code and update user info
            existing_user_by_email.dogrulama_kodu = rastgele_kod()
            existing_user_by_email.kod_zaman = datetime.now()
            existing_user_by_email.ad = ad
            existing_user_by_email.soyad = soyad
            existing_user_by_email.username = username
            existing_user_by_email.sifre = generate_password_hash(sifre)
            existing_user_by_email.telefon = telefon
            existing_user_by_email.tc_no = tc_no
            existing_user_by_email.adres = adres
            existing_user_by_email.dogum_tarihi = dogum_tarihi
            existing_user_by_email.rol = rol
            existing_user_by_email.cinsiyet = cinsiyet # Cinsiyeti de güncelle
            db.session.commit()
            send_verification_email(existing_user_by_email.email, existing_user_by_email.dogrulama_kodu)
            session['dogrulama_email'] = existing_user_by_email.email
            flash('Bu e-posta adresi zaten kayıtlı ancak doğrulanmamış. Bilgileriniz güncellendi ve yeni bir doğrulama kodu gönderildi.', 'info')
            return redirect(url_for('dogrulama_sayfasi'))
        else:
            flash('Bu e-posta zaten kayıtlı ve doğrulanmış. Lütfen giriş yapın.', 'error')
            return render_template('register.html', form_data=form_data)
    
    if existing_user_by_username:
        if not existing_user_by_username.dogrulandi_mi:
            # User exists but not verified, resend code and update user info
            existing_user_by_username.dogrulama_kodu = rastgele_kod()
            existing_user_by_username.kod_zaman = datetime.now()
            existing_user_by_username.ad = ad
            existing_user_by_username.soyad = soyad
            existing_user_by_username.email = email
            existing_user_by_username.sifre = generate_password_hash(sifre)
            existing_user_by_username.telefon = telefon
            existing_user_by_username.tc_no = tc_no
            existing_user_by_username.adres = adres
            existing_user_by_username.dogum_tarihi = dogum_tarihi
            existing_user_by_username.rol = rol
            existing_user_by_username.cinsiyet = cinsiyet # Cinsiyeti de güncelle
            db.session.commit()
            send_verification_email(existing_user_by_username.email, existing_user_by_username.dogrulama_kodu)
            session['dogrulama_email'] = existing_user_by_username.email
            flash('Bu kullanıcı adı zaten alınmış ancak doğrulanmamış. Bilgileriniz güncellendi ve yeni bir doğrulama kodu gönderildi.', 'info')
            return redirect(url_for('dogrulama_sayfasi'))
        else:
            flash('Bu kullanıcı adı zaten alınmış ve doğrulanmış. Lütfen giriş yapın.', 'error')
            return render_template('register.html', form_data=form_data)

    # If all validations pass and user is new, create and save (unverified)
    hashed_password = generate_password_hash(sifre)

    yeni_kullanici = Kullanici(
        ad=ad,
        soyad=soyad,
        username=username,
        email=email,
        sifre=hashed_password,
        telefon=telefon,
        tc_no=tc_no,
        adres=adres,
        dogum_tarihi=dogum_tarihi,
        dogrulandi_mi=False, # Initially False, will be True after verification
        dogrulama_kodu=rastgele_kod(),
        kod_zaman=datetime.now(),
        rol=rol,
        cinsiyet=cinsiyet # Cinsiyeti kaydet
    )
    
    db.session.add(yeni_kullanici)
    try:
        db.session.commit() # Save to DB as unverified
        send_verification_email(email, yeni_kullanici.dogrulama_kodu)
        
        session['dogrulama_email'] = email
        flash('Kaydınız başarıyla alındı. Lütfen e-postanıza gönderilen doğrulama kodunu girin.', 'success')
        return redirect(url_for('dogrulama_sayfasi'))
    except Exception as e:
        db.session.rollback()
        print(f"VERİTABANI KAYDETME HATASI (Kayıt): {e}")
        flash("Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.", 'error')
        return render_template('register.html', form_data=form_data) # Hata durumunda formu doldurulmuş olarak geri gönder

# Verification Page
@app.route('/dogrulama')
def dogrulama_sayfasi():
    if 'dogrulama_email' not in session:
        flash('Doğrulama işlemi için e-posta adresi bulunamadı veya oturum süresi doldu. Lütfen tekrar kayıt olun.', 'info')
        return redirect(url_for('index'))
    return render_template('verify.html', email=session.get('dogrulama_email', ''))

# Verification Process
@app.route('/dogrula', methods=['POST'])
def dogrula():
    email = session.get('dogrulama_email')
    if not email:
        flash('Doğrulama için e-posta bulunamadı. Lütfen tekrar kayıt olun.', 'error')
        return redirect(url_for('index'))
    
    kullanici = Kullanici.query.filter_by(email=email).first()
    if not kullanici:
        flash('Kullanıcı bulunamadı.', 'error')
        return redirect(url_for('index'))
    
    # Code expiration check (10 minutes)
    if datetime.now() > kullanici.kod_zaman + timedelta(minutes=10):
        flash('Kod süresi doldu! Lütfen tekrar kayıt olun.', 'error')
        session.pop('dogrulama_email', None) # Clear expired code
        return redirect(url_for('index'))
    
    if request.form['kod'] == kullanici.dogrulama_kodu:
        kullanici.dogrulandi_mi = True
        kullanici.dogrulama_kodu = None # Kodu kullandıktan sonra temizle
        kullanici.kod_zaman = None # Zamanı temizle
        db.session.commit()
        session.pop('dogrulama_email', None)
        flash('Hesabınız başarıyla doğrulandı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('giris_sayfasi'))
    else:
        flash('Geçersiz doğrulama kodu!', 'error')
        return redirect(url_for('dogrulama_sayfasi'))

# Resend Verification Code
@app.route('/kodu_yeniden_gonder', methods=['GET'])
def resend_verification_code():
    email = session.get('dogrulama_email')
    if not email:
        flash('Doğrulama kodu göndermek için bir e-posta adresi bulunamadı. Lütfen tekrar kayıt olun.', 'error')
        return redirect(url_for('index'))
    
    kullanici = Kullanici.query.filter_by(email=email).first() # Doğrulanmış veya doğrulanmamış fark etmez
    if not kullanici:
        flash('Kullanıcı bulunamadı.', 'error')
        return redirect(url_for('index'))

    if kullanici.dogrulandi_mi:
        flash('Hesabınız zaten doğrulanmış. Giriş yapabilirsiniz.', 'info')
        session.pop('dogrulama_email', None)
        return redirect(url_for('giris_sayfasi'))
    
    # Generate new code and update time in DB
    kullanici.dogrulama_kodu = rastgele_kod()
    kullanici.kod_zaman = datetime.now()
    db.session.commit()

    send_verification_email(kullanici.email, kullanici.dogrulama_kodu)
    flash('Yeni doğrulama kodu e-posta adresinize gönderildi.', 'success')
    return redirect(url_for('dogrulama_sayfasi'))


# Login Page
@app.route('/giris')
def giris_sayfasi():
    return render_template('login.html')

# Login Process - KULLANICI ROLÜ OTURUMA KAYDEDİLDİ
@app.route('/giris_yap', methods=['POST'])
def giris_yap():
    veri = request.form
    user_identifier = veri.get('user_identifier', '').strip().lower()
    sifre = veri.get('sifre', '')

    if not user_identifier or not sifre:
        flash('Kullanıcı adı/E-posta ve şifre boş bırakılamaz.', 'error')
        return redirect(url_for('giris_sayfasi'))

    # Find user by email or username
    kullanici = Kullanici.query.filter_by(email=user_identifier).first()
    if not kullanici:
        kullanici = Kullanici.query.filter_by(username=user_identifier).first()
    
    if kullanici:
        # Check hashed password
        if check_password_hash(kullanici.sifre, sifre):
            if kullanici.dogrulandi_mi:
                session['giris_yapildi'] = True
                session['kullanici_email'] = kullanici.email
                session['kullanici_rol'] = kullanici.rol # Kullanıcı rolünü oturuma kaydet
                flash(f'Hoş geldiniz, {kullanici.ad} {kullanici.soyad}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Hesabınız doğrulanmamış! Lütfen e-postanızı kontrol edin ve doğrulayın.', 'error')
                session['dogrulama_email'] = kullanici.email
                return redirect(url_for('dogrulama_sayfasi'))
        else:
            flash('Geçersiz şifre!', 'error')
            return redirect(url_for('giris_sayfasi'))
    else:
        flash('Kullanıcı adı veya e-posta bulunamadı!', 'error')
        return redirect(url_for('giris_sayfasi'))

# Dashboard - ROL BİLGİSİ GÖSTERİLDİ
@app.route('/dashboard')
def dashboard():
    if not session.get('giris_yapildi'):
        flash('Giriş yapmanız gerekiyor.', 'info')
        return redirect(url_for('giris_sayfasi'))
    
    kullanici = Kullanici.query.filter_by(email=session.get('kullanici_email')).first()
    if not kullanici:
        flash('Kullanıcı bilgileri bulunamadı, lütfen tekrar giriş yapın.', 'error')
        return redirect(url_for('cikis'))
    
    return render_template('dashboard.html', kullanici=kullanici)

# Logout
@app.route('/cikis')
def cikis():
    session.pop('giris_yapildi', None)
    session.pop('kullanici_email', None)
    session.pop('kullanici_rol', None) # Rolü de oturumdan temizle
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('giris_sayfasi'))

# Forgot Password Request Page
@app.route('/sifre_sifirla', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        kullanici = Kullanici.query.filter_by(email=email).first()
        if kullanici:
            token = s.dumps(email, salt='password-reset-salt')
            kullanici.reset_token = token
            kullanici.reset_token_expiry = datetime.now() + timedelta(hours=1) # Token valid for 1 hour
            db.session.commit()
            send_password_reset_email(email, token)
            flash('Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.', 'success')
            return redirect(url_for('giris_sayfasi'))
        else:
            flash('Bu e-posta adresiyle kayıtlı bir kullanıcı bulunamadı.', 'error')
    return render_template('forgot_password.html')

# Password Reset Token Validation and New Password Setting Page
@app.route('/sifre_sifirla/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    email = None
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600) # Validate token within 1 hour
    except SignatureExpired:
        flash('Şifre sıfırlama bağlantısının süresi doldu. Lütfen tekrar talep edin.', 'error')
        return redirect(url_for('forgot_password'))
    except BadTimeSignature:
        flash('Geçersiz şifre sıfırlama bağlantısı.', 'error')
        return redirect(url_for('forgot_password'))

    kullanici = Kullanici.query.filter_by(email=email).first()
    if not kullanici or kullanici.reset_token != token or \
       (kullanici.reset_token_expiry and kullanici.reset_token_expiry < datetime.now()):
        flash('Geçersiz veya süresi dolmuş şifre sıfırlama bağlantısı.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if new_password != confirm_password:
            flash('Şifreler uyuşmuyor.', 'error')
            return render_template('reset_password.html', token=token)
        
        password_strength_error = check_password_strength(new_password)
        if password_strength_error:
            flash(password_strength_error, 'error')
            return render_template('reset_password.html', token=token)

        kullanici.sifre = generate_password_hash(new_password)
        kullanici.reset_token = None
        kullanici.reset_token_expiry = None
        db.session.commit()
        flash('Şifreniz başarıyla sıfırlandı. Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('giris_sayfasi'))

    return render_template('reset_password.html', token=token)

# Create database tables when the application starts
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()  # Create database tables
    app.run(debug=True)
