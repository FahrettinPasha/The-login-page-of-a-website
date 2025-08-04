// register.js
var map;
var marker;
var selectedLat;
var selectedLng;
const currentLocationDisplay = document.getElementById('current-location-display'); // Konum bilgisinin gösterileceği span

// Harita modalını gösteren ve haritayı başlatan/güncelleyen fonksiyon
function showLocation() {
    var mapModal = document.getElementById('map-modal');
    mapModal.style.display = 'flex'; // Modalı göster

    // Harita zaten başlatıldıysa, sadece boyutunu güncelle
    if (map) {
        map.invalidateSize();
    }

    // Eğer daha önce bir konum seçildiyse, haritayı o konuma odakla
    if (selectedLat && selectedLng) {
        initializeOrUpdateMap(selectedLat, selectedLng);
    } else {
        // İlk açılışta veya konum seçilmemişse varsayılan olarak Mersin'e odakla
        initializeOrUpdateMap(36.8121, 34.6415); // Mersin koordinatları
    }
    // Modalı açtığımızda mevcut adres inputundaki değeri göster
    currentLocationDisplay.textContent = document.getElementById('adres').value || 'Konum bekleniyor...';
}

// Kullanıcının mevcut konumunu bulan fonksiyon
async function locateUser() {
    if (navigator.geolocation) {
        currentLocationDisplay.textContent = 'Konumunuz bulunuyor...';
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 });
            });
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            initializeOrUpdateMap(lat, lng);
            
            // Konum bulunduğunda adres bilgisini çek
            const nominatimUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`;
            const response = await fetch(nominatimUrl);
            const data = await response.json();
            if (data && data.display_name) {
                currentLocationDisplay.textContent = data.display_name;
                flash('Konumunuz başarıyla bulundu.', 'success');
            } else {
                currentLocationDisplay.textContent = `Konum: ${lat}, ${lng}`;
                flash('Konumunuz bulundu ancak adres bilgisi alınamadı.', 'info');
            }
        } catch (error) {
            console.error("Konum alınamadı:", error);
            currentLocationDisplay.textContent = 'Konum alınamadı.';
            flash('Konumunuz alınamadı. Lütfen konum izni verdiğinizden emin olun veya haritayı manuel olarak kullanın.', 'error');
            // Konum alınamazsa varsayılan konuma geri dön veya mevcut konumu koru
            if (!selectedLat || !selectedLng) {
                initializeOrUpdateMap(36.8121, 34.6415); // Mersin koordinatları
            }
        }
    } else {
        currentLocationDisplay.textContent = 'Tarayıcınız konum servislerini desteklemiyor.';
        flash('Tarayıcınız konum servislerini desteklemiyor.', 'error');
    }
}

// Haritayı başlatan veya güncelleyen ana fonksiyon
function initializeOrUpdateMap(lat, lng) {
    if (!map) {
        // Harita henüz başlatılmadıysa, başlat
        map = L.map('map').setView([lat, lng], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        map.on('click', async function(e) { // Asenkron yapıldı
            selectedLat = e.latlng.lat;
            selectedLng = e.latlng.lng;
            if (marker) {
                marker.setLatLng(e.latlng);
            } else {
                marker = L.marker(e.latlng).addTo(map);
            }
            document.getElementById('confirmLocationBtn').disabled = false; // Konum seçildiğinde butonu etkinleştir
            
            // Tıklanan konumun adresini göster
            const nominatimUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${selectedLat}&lon=${selectedLng}`;
            try {
                const response = await fetch(nominatimUrl);
                const data = await response.json();
                if (data && data.display_name) {
                    currentLocationDisplay.textContent = data.display_name;
                } else {
                    currentLocationDisplay.textContent = `Seçilen Konum: ${selectedLat}, ${selectedLng}`;
                }
            } catch (error) {
                console.error('Adres bilgisi alınırken hata oluştu:', error);
                currentLocationDisplay.textContent = `Seçilen Konum: ${selectedLat}, ${selectedLng}`;
            }
        });
    } else {
        // Harita zaten başlatıldıysa, sadece görünümünü ayarla
        map.setView([lat, lng], 13);
        if (marker) {
            marker.setLatLng([lat, lng]);
        } else {
            marker = L.marker([lat, lng]).addTo(map);
        }
    }
    // Harita güncellendiğinde veya yeni konum alındığında seçili konumu güncelle ve onay butonunu etkinleştir
    selectedLat = lat;
    selectedLng = lng;
    document.getElementById('confirmLocationBtn').disabled = false;
}

function closeMapModal() {
    var mapModal = document.getElementById('map-modal');
    mapModal.style.display = 'none'; // Modalı gizle
    currentLocationDisplay.textContent = ''; // Modalı kapatırken metni temizle
}

async function confirmAddress() {
    if (selectedLat && selectedLng) {
        document.getElementById('latitude').value = selectedLat;
        document.getElementById('longitude').value = selectedLng;

        // Seçilen koordinatlardan adres bilgisini al
        const nominatimUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${selectedLat}&lon=${selectedLng}`;
        try {
            const response = await fetch(nominatimUrl);
            const data = await response.json();
            if (data && data.display_name) {
                document.getElementById('adres').value = data.display_name;
                applyValidationAndIcon(document.getElementById('adres')); // Adres güncellendiğinde ikon güncelle
            } else {
                document.getElementById('adres').value = `Seçilen Konum: ${selectedLat}, ${selectedLng}`;
            }
        } catch (error) {
            console.error('Adres bilgisi alınırken hata oluştu:', error);
            document.getElementById('adres').value = `Seçilen Konum: ${selectedLat}, ${selectedLng}`;
        }
        closeMapModal();
    } else {
        // Modalı kapatmadan önce kullanıcıya uyarı göster
        flash('Lütfen harita üzerinde bir konum seçin.', 'error');
    }
}

// intl-tel-input başlatılıyor
const phoneInputField = document.getElementById("telefon");
const iti = window.intlTelInput(phoneInputField, {
    utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
    initialCountry: "tr", // Varsayılan ülke Türkiye
    onlyCountries: ["tr"], // Sadece Türkiye'yi göster
    separateDialCode: false, // Ülke kodunu inputtan ayırma (input içinde +90 vs. görünecek)
    dropdownContainer: document.body, // Menüyü doğrudan body'ye ekle
});

// Eğer telefon inputunda önceden doldurulmuş bir değer varsa, intl-tel-input'a bildir
if (phoneInputField.value) {
    iti.setNumber(phoneInputField.value);
}

// Şifre gücü kontrolü için JavaScript
const passwordInput = document.getElementById('sifre');
const confirmPasswordInput = document.getElementById('confirm_sifre'); // Yeni şifre onay alanı
const passwordFeedback = document.getElementById('password-strength-feedback');
const passwordStrengthBarContainer = document.querySelector('.password-strength-bar-container');
const passwordStrengthBar = document.getElementById('password-strength-bar');
const passwordIcon = passwordInput.closest('.input-group').querySelector('.input-feedback-icon');
const confirmPasswordIcon = confirmPasswordInput.closest('.input-group').querySelector('.input-feedback-icon'); // Şifre onay ikonu

function updatePasswordStrength() {
    const password = passwordInput.value;
    
    // Hide bar and feedback if password is empty
    if (password.length === 0) {
        passwordFeedback.classList.add('hidden');
        passwordStrengthBarContainer.classList.add('hidden');
        passwordIcon.classList.remove('valid-icon', 'invalid-icon');
        passwordIcon.textContent = '';
        return; // Stop further processing
    } else {
        passwordFeedback.classList.remove('hidden');
        passwordStrengthBarContainer.classList.remove('hidden');
    }

    let strength = 0; // Score from 0-5
    let feedbackText = '';
    let feedbackClass = '';
    let barWidth = 0;

    const hasMinLength = password.length >= 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    if (hasMinLength) strength++;
    if (hasUpperCase) strength++;
    if (hasLowerCase) strength++;
    if (hasDigit) strength++;
    if (hasSpecialChar) strength++;

    if (strength < 3) {
        feedbackText = 'Şifre çok zayıf! (En az 8 karakter, B/k harf, rakam, özel karakter önerilir)';
        feedbackClass = 'weak';
        barWidth = (strength / 5) * 100;
        passwordIcon.classList.remove('valid-icon');
        passwordIcon.classList.add('invalid-icon');
        passwordIcon.textContent = '✕'; // Red cross
    } else if (strength >=3 && strength < 5) { // Orta düzey şifreler için (3 veya 4 kriter)
        feedbackText = 'Şifre orta güçlükte.';
        feedbackClass = 'medium';
        barWidth = (strength / 5) * 100;
        passwordIcon.classList.remove('invalid-icon'); // Orta düzeyde de tik göster
        passwordIcon.classList.add('valid-icon');
        passwordIcon.textContent = '✓'; // Green tick
    } else { // strength === 5
        feedbackText = 'Şifre güçlü!';
        feedbackClass = 'strong';
        barWidth = 100;
        passwordIcon.classList.remove('invalid-icon');
        passwordIcon.classList.add('valid-icon');
        passwordIcon.textContent = '✓'; // Green tick
    }

    passwordFeedback.textContent = feedbackText;
    passwordFeedback.className = 'password-feedback ' + feedbackClass;

    passwordStrengthBar.style.width = barWidth + '%';
    passwordStrengthBar.className = 'password-strength-bar ' + feedbackClass;
}

function validateConfirmPassword() {
    if (confirmPasswordInput.value.length === 0) {
        confirmPasswordInput.classList.remove('is-valid', 'is-invalid');
        confirmPasswordIcon.classList.remove('valid-icon', 'invalid-icon');
        confirmPasswordIcon.textContent = '';
        return;
    }

    if (passwordInput.value === confirmPasswordInput.value) {
        confirmPasswordInput.classList.remove('is-invalid');
        confirmPasswordInput.classList.add('is-valid');
        confirmPasswordIcon.classList.remove('invalid-icon');
        confirmPasswordIcon.classList.add('valid-icon');
        confirmPasswordIcon.textContent = '✓';
    } else {
        confirmPasswordInput.classList.remove('is-valid');
        confirmPasswordInput.classList.add('is-invalid');
        confirmPasswordIcon.classList.remove('valid-icon');
        confirmPasswordIcon.classList.add('invalid-icon');
        confirmPasswordIcon.textContent = '✕';
    }
}

passwordInput.addEventListener('input', function() {
    updatePasswordStrength();
    validateConfirmPassword(); // Şifre değişince onay şifresini de kontrol et
});
confirmPasswordInput.addEventListener('input', validateConfirmPassword);


// Genel input doğrulama ve ikon gösterme
const inputsToValidate = [
    document.getElementById('ad'),
    document.getElementById('soyad'),
    document.getElementById('username'),
    document.getElementById('email'),
    document.getElementById('telefon'),
    document.getElementById('tc_no'),
    document.getElementById('adres'),
    document.getElementById('rol') // Rol seçim alanı eklendi
];

function applyValidationAndIcon(inputElement) {
    const iconElement = inputElement.closest('.input-group').querySelector('.input-feedback-icon');
    if (!iconElement) return;

    if (inputElement.value.length === 0 || (inputElement.tagName === 'SELECT' && inputElement.value === '')) {
        inputElement.classList.remove('is-valid', 'is-invalid');
        iconElement.classList.remove('valid-icon', 'invalid-icon');
        iconElement.textContent = '';
    } else if (inputElement.checkValidity()) {
        inputElement.classList.remove('is-invalid');
        inputElement.classList.add('is-valid');
        iconElement.classList.remove('invalid-icon');
        iconElement.classList.add('valid-icon');
        iconElement.textContent = '✓'; // Green tick
    } else {
        inputElement.classList.remove('is-valid');
        inputElement.classList.add('is-invalid');
        iconElement.classList.remove('valid-icon');
        iconElement.classList.add('invalid-icon');
        iconElement.textContent = '✕'; // Red cross
    }
}

inputsToValidate.forEach(input => {
    if (input) {
        input.addEventListener('input', function() {
            applyValidationAndIcon(this);
        });
        if (input.tagName === 'SELECT') { // Select elementleri için 'change' event'i ekle
            input.addEventListener('change', function() {
                applyValidationAndIcon(this);
            });
        }
    }
});

// Telefon numarası için özel doğrulama ve ikon gösterme (intl-tel-input ile)
phoneInputField.addEventListener('input', function() {
    const inputElement = this;
    const iconElement = inputElement.closest('.input-group').querySelector('.input-feedback-icon');
    if (!iconElement) return;

    // intl-tel-input'un geçerli numara kontrolünü kullan
    if (iti.isValidNumber()) {
        inputElement.classList.remove('is-invalid');
        inputElement.classList.add('is-valid');
        iconElement.classList.remove('invalid-icon');
        iconElement.classList.add('valid-icon');
        iconElement.textContent = '✓';
    } else {
        inputElement.classList.remove('is-valid');
        inputElement.classList.add('is-invalid');
        iconElement.classList.remove('valid-icon');
        iconElement.classList.add('invalid-icon');
        iconElement.textContent = '✕';
    }
    if (inputElement.value.length === 0) { // Boşsa ikonu kaldır
        inputElement.classList.remove('is-valid', 'is-invalid');
        iconElement.classList.remove('valid-icon', 'invalid-icon');
        iconElement.textContent = '';
    }
});


// Doğum tarihi için özel doğrulama ve ikon gösterme
const dogumTarihiInput = document.getElementById('dogum_tarihi');

function validateDogumTarihi() {
    const inputElement = dogumTarihiInput;
    const iconElement = inputElement.closest('.input-group').querySelector('.input-feedback-icon');
    if (!iconElement) return;

    if (inputElement.value.length === 0) {
        inputElement.classList.remove('is-valid', 'is-invalid');
        iconElement.classList.remove('valid-icon', 'invalid-icon');
        iconElement.textContent = '';
        return;
    }

    const birthDateStr = inputElement.value;
    const birthDate = new Date(birthDateStr);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }

    // Prevent future dates
    if (birthDate > today) {
        inputElement.classList.remove('is-valid');
        inputElement.classList.add('is-invalid');
        iconElement.classList.remove('valid-icon');
        iconElement.classList.add('invalid-icon');
        iconElement.textContent = '✕';
        return;
    }

    // 18 years old check
    if (age < 18) {
        inputElement.classList.remove('is-valid');
        inputElement.classList.add('is-invalid');
        iconElement.classList.remove('valid-icon');
        iconElement.classList.add('invalid-icon');
        iconElement.textContent = '✕';
    } else {
        inputElement.classList.remove('is-invalid');
        inputElement.classList.add('is-valid');
        iconElement.classList.remove('invalid-icon');
        iconElement.classList.add('valid-icon');
        iconElement.textContent = '✓';
    }
}

dogumTarihiInput.addEventListener('input', validateDogumTarihi);
dogumTarihiInput.addEventListener('change', validateDogumTarihi); // Check when date picker changes

// Sayfa yüklendiğinde varsayılan değerler için stil ve ikon uygula
document.addEventListener('DOMContentLoaded', function() {
    inputsToValidate.forEach(input => {
        if (input) {
            applyValidationAndIcon(input);
        }
    });
    // Initial validation for phone number
    phoneInputField.dispatchEvent(new Event('input')); 
    updatePasswordStrength(); // Şifre gücü geri bildirimini başlat
    validateConfirmPassword(); // Şifre onayını başlat
    validateDogumTarihi(); // Initial validation for birth date
});

// Form gönderilmeden önce son kontroller
const registerForm = document.getElementById('registerForm');
registerForm.addEventListener('submit', function(event) {
    // Şifre gücü kontrolü: Zayıfsa göndermeyi engelle
    const password = passwordInput.value;
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;

    if (strength < 3) { // 3'ten az ise zayıf kabul et
        event.preventDefault();
        flash('Şifreniz çok zayıf! Lütfen daha güçlü bir şifre belirleyin.', 'error');
        passwordInput.focus();
        return;
    }

    // Şifrelerin eşleşme kontrolü
    if (passwordInput.value !== confirmPasswordInput.value) {
        event.preventDefault();
        flash('Şifreler eşleşmiyor! Lütfen aynı şifreyi tekrar girin.', 'error');
        confirmPasswordInput.focus();
        return;
    }

    // Telefon numarası doğrulaması (intl-tel-input'tan gelen geçerlilik kontrolü)
    if (!iti.isValidNumber()) {
        event.preventDefault();
        flash('Lütfen geçerli bir telefon numarası giriniz.', 'error');
        phoneInputField.focus();
        return;
    }

    // Doğum tarihi kontrolü
    const birthDateStr = dogumTarihiInput.value;
    const birthDate = new Date(birthDateStr);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }

    if (birthDate > today) {
        event.preventDefault();
        flash('Doğum tarihi gelecekte olamaz.', 'error');
        dogumTarihiInput.focus();
        return;
    }
    if (age < 18) {
        event.preventDefault();
        flash('Kayıt olmak için 18 yaşından büyük olmalısınız.', 'error');
        dogumTarihiInput.focus();
        return;
    }

    // Rol seçimi kontrolü
    const rolSelect = document.getElementById('rol');
    if (rolSelect.value === '') {
        event.preventDefault();
        flash('Lütfen kullanıcı rolünüzü seçin.', 'error');
        rolSelect.focus();
        return;
    }
});

// Basit bir flash mesaj fonksiyonu (Flask'ın flash'ı gibi çalışmaz, sadece örnek)
function flash(message, category) {
    const flashesDiv = document.querySelector('.flashes');
    if (flashesDiv) {
        const li = document.createElement('li');
        li.className = category;
        li.textContent = message;
        flashesDiv.appendChild(li);
        setTimeout(() => {
            li.remove();
        }, 5000); // 5 saniye sonra kaldır
    }
}
