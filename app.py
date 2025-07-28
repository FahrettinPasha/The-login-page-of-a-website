from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import random
import string
from datetime import datetime, timedelta
import os
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash # Şifre hashleme için eklendi

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cok_gizli_bir_anahtar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail yapılandırması
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'karacemalopsiyonel@gmail.com'  # GMAIL adresiniz
app.config['MAIL_PASSWORD'] = 'yjvf wjii iofc jnwo'      # Google App Şifresi

mail = Mail(app) # Mail nesnesi başlatıldı

db = SQLAlchemy(app)

# Kullanıcı Modeli
class Kullanici(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False) # Yeni: Kullanıcı adı alanı
    email = db.Column(db.String(100), unique=True, nullable=False)
    sifre = db.Column(db.String(255), nullable=False) # Şifre hash'i için uzunluk artırıldı
    telefon = db.Column(db.String(20), nullable=False) # Nullable=False yapıldı
    tc_no = db.Column(db.String(11), nullable=False) # Nullable=False yapıldı
    adres = db.Column(db.Text)
    dogrulandi_mi = db.Column(db.Boolean, default=False)
    dogrulama_kodu = db.Column(db.String(6))
    kod_zaman = db.Column(db.DateTime)

# Rastgele 6 haneli kod üretme
def rastgele_kod():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# E-posta gönderme fonksiyonu
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
        flash(f"Doğrulama e-postası gönderilemedi: {e}", 'error') # Hata mesajını flash ile göster

# Ana Sayfa (Kayıt Formu)
@app.route('/')
def index():
    return render_template('register.html')

# Kayıt İşlemi
@app.route('/kayit', methods=['POST'])
def kayit():
    veri = request.form
    ad_soyad = veri.get('ad_soyad', '').strip()
    username = veri.get('username', '').strip()
    email = veri.get('email', '').strip()
    sifre = veri.get('sifre', '')
    telefon = veri.get('telefon', '').strip()
    tc_no = veri.get('tc_no', '').strip()
    adres = veri.get('adres', '').strip()

    # Sunucu tarafı doğrulama
    if not ad_soyad:
        flash('Ad Soyad boş bırakılamaz.', 'error')
        return redirect(url_for('index'))
    if not username or len(username) < 3:
        flash('Kullanıcı adı en az 3 karakter olmalıdır.', 'error')
        return redirect(url_for('index'))
    if not email or '@' not in email or '.' not in email:
        flash('Geçerli bir e-posta adresi giriniz.', 'error')
        return redirect(url_for('index'))
    if not sifre or len(sifre) < 6:
        flash('Şifre en az 6 karakter olmalıdır.', 'error')
        return redirect(url_for('index'))
    # Telefon numarası için daha sıkı kontrol
    if not telefon or not telefon.isdigit() or len(telefon) < 10 or len(telefon) > 15: # Örnek: 10-15 hane arası
        flash('Geçerli bir telefon numarası giriniz (sadece rakamlar, 10-15 hane arası).', 'error')
        return redirect(url_for('index'))
    # TC Kimlik No için sıkı kontrol
    if not tc_no or not tc_no.isdigit() or len(tc_no) != 11:
        flash('TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır.', 'error')
        return redirect(url_for('index'))

    # E-posta ve Kullanıcı adı benzersizlik kontrolü
    if Kullanici.query.filter_by(email=email).first():
        flash('Bu e-posta zaten kayıtlı!', 'error')
        return redirect(url_for('index'))
    if Kullanici.query.filter_by(username=username).first():
        flash('Bu kullanıcı adı zaten alınmış!', 'error')
        return redirect(url_for('index'))

    # Şifreyi hash'le
    hashed_password = generate_password_hash(sifre)

    yeni_kullanici = Kullanici(
        ad_soyad=ad_soyad,
        username=username,
        email=email,
        sifre=hashed_password, # Hashlenmiş şifreyi kaydet
        telefon=telefon,
        tc_no=tc_no,
        adres=adres,
        dogrulama_kodu=rastgele_kod(),
        kod_zaman=datetime.now()
    )
    
    db.session.add(yeni_kullanici)
    db.session.commit()
    
    send_verification_email(yeni_kullanici.email, yeni_kullanici.dogrulama_kodu)
    
    session['dogrulama_email'] = email
    flash('Kaydınız başarıyla alındı. Lütfen e-postanıza gönderilen doğrulama kodunu girin.', 'success')
    return redirect(url_for('dogrulama_sayfasi'))

# Doğrulama Sayfası
@app.route('/dogrulama')
def dogrulama_sayfasi():
    return render_template('verify.html', email=session.get('dogrulama_email', ''))

# Doğrulama İşlemi
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
    
    # Kod süresi kontrolü (10 dakika)
    if datetime.now() > kullanici.kod_zaman + timedelta(minutes=10):
        flash('Kod süresi doldu! Lütfen tekrar kayıt olun.', 'error')
        return redirect(url_for('index'))
    
    if request.form['kod'] == kullanici.dogrulama_kodu:
        kullanici.dogrulandi_mi = True
        db.session.commit()
        session.pop('dogrulama_email', None)
        flash('Hesabınız başarıyla doğrulandı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('giris_sayfasi'))
    else:
        flash('Geçersiz doğrulama kodu!', 'error')
        return redirect(url_for('dogrulama_sayfasi'))

# Giriş Sayfası
@app.route('/giris')
def giris_sayfasi():
    return render_template('login.html')

# Giriş İşlemi
@app.route('/giris_yap', methods=['POST'])
def giris_yap():
    veri = request.form
    user_identifier = veri.get('user_identifier', '').strip() # Kullanıcı adı veya e-posta
    sifre = veri.get('sifre', '')

    if not user_identifier or not sifre:
        flash('Kullanıcı adı/E-posta ve şifre boş bırakılamaz.', 'error')
        return redirect(url_for('giris_sayfasi'))

    # Kullanıcıyı e-posta veya kullanıcı adına göre bul
    kullanici = Kullanici.query.filter_by(email=user_identifier).first()
    if not kullanici:
        kullanici = Kullanici.query.filter_by(username=user_identifier).first()
    
    if kullanici:
        # Hashlenmiş şifreyi kontrol et
        if check_password_hash(kullanici.sifre, sifre):
            if kullanici.dogrulandi_mi:
                session['giris_yapildi'] = True
                session['kullanici_email'] = kullanici.email  # Oturum takibi için e-postayı kullanmaya devam et
                flash(f'Hoş geldiniz, {kullanici.ad_soyad}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Hesabınız doğrulanmamış! Lütfen e-postanızı kontrol edin ve doğrulayın.', 'error')
                session['dogrulama_email'] = kullanici.email # Doğrulama sayfasına yönlendirmek için e-postayı ayarla
                return redirect(url_for('dogrulama_sayfasi'))
        else:
            flash('Geçersiz şifre!', 'error')
            return redirect(url_for('giris_sayfasi'))
    else:
        flash('Kullanıcı adı veya e-posta bulunamadı!', 'error')
        return redirect(url_for('giris_sayfasi'))

# Dashboard
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

# Çıkış Yap
@app.route('/cikis')
def cikis():
    session.pop('giris_yapildi', None)
    session.pop('kullanici_email', None)
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('giris_sayfasi'))

# Veritabanını uygulama başlatıldığında oluştur
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()  # Veritabanı tablolarını oluştur
    app.run(debug=True)
