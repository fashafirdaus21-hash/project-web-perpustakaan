from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "kunci_rahasia_perpustakaan"

# Menghubungkan ke koneksi.py
try:
    from koneksi import koneksi_db
except ImportError:
    koneksi_db = None

@app.route('/')
def index():
    return redirect(url_for('login'))

# --- HALAMAN LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_user = request.form.get('id_user')
        password = request.form.get('password')
        
        # CETAK DEBUG KE TERMINAL
        print(f"--- COBA LOGIN ---")
        print(f"ID yang diinput dari web: '{id_user}'")
        print(f"Password yang diinput dari web: '{password}'")
        
        if koneksi_db:
            try:
                db = koneksi_db()
                cursor = db.cursor(dictionary=True)
                
                query = "SELECT * FROM users WHERE id_user = %s AND password_hash = %s"
                cursor.execute(query, (id_user, password))
                user = cursor.fetchone()
                
                print(f"Hasil pencarian di database: {user}")
                
                cursor.close()
                db.close()
                
                if user:
                    session['id_user'] = user['id_user']
                    session['nama'] = user['nama']
                    session['role'] = user['role']
                    
                    print(f"Login Berhasil! Role: {user['role']}")
                    
                    if user['role'] in ['admin', 'programmer']:
                        return redirect(url_for('admin_dashboard'))
                    elif user['role'] == 'kepsek':
                        return redirect(url_for('kepsek_dashboard'))
                    elif user['role'] == 'siswa':
                        return redirect(url_for('user_dashboard'))
                else:
                    print("Status: User tidak ditemukan atau password salah!")
            except Exception as e:
                print(f"Error Database: {e}")
                
    return render_template('login.html', pesan="ID atau Password salah!")

# --- HALAMAN REGISTRASI ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_user = request.form.get('id_user')
        email = request.form.get('email')
        password = request.form.get('password')
        nama = request.form.get('nama')
        role = request.form.get('role', 'siswa')  # Default role terdaftar sebagai siswa
        
        if koneksi_db:
            try:
                db = koneksi_db()
                cursor = db.cursor()
                query = "INSERT INTO users (id_user, email, password_hash, nama, role) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (id_user, email, password, nama, role))
                db.commit()
                cursor.close()
                db.close()
            except Exception as e:
                print(f"Error Register: {e}")
                
        return redirect(url_for('login'))
        
    return render_template('register.html')


# ==========================================
# --- RUTE DASHBOARD: ADMIN & PROGRAMMER ---
# ==========================================
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') in ['admin', 'programmer']:
        return render_template('admin/dashboard.html')
    return redirect(url_for('login'))

@app.route('/admin/kelola-buku')
def admin_kelola_buku():
    if session.get('role') in ['admin', 'programmer']:
        return render_template('admin/kelolabuku.html')
    return redirect(url_for('login'))

@app.route('/admin/peminjaman')
def admin_peminjaman():
    if session.get('role') in ['admin', 'programmer']:
        return render_template('admin/peminjaman.html')
    return redirect(url_for('login'))

@app.route('/admin/pengembalian')
def admin_pengembalian():
    if session.get('role') in ['admin', 'programmer']:
        return render_template('admin/pengembalian.html')
    return redirect(url_for('login'))

@app.route('/admin/biodata')
def admin_biodata():
    if session.get('role') in ['admin', 'programmer']:
        return render_template('admin/biodataagt.html')
    return redirect(url_for('login'))


# ==========================================
# --- RUTE DASHBOARD: KEPALA SEKOLAH ---
# ==========================================
@app.route('/kepsek/dashboard')
def kepsek_dashboard():
    if session.get('role') == 'kepsek':
        return render_template('kepsek/dashboard.html')
    return redirect(url_for('login'))

@app.route('/kepsek/laporan')
def kepsek_laporan():
    if session.get('role') == 'kepsek':
        return render_template('kepsek/laporan.html')
    return redirect(url_for('login'))


# ==========================================
# --- RUTE DASHBOARD: SISWA / USER ---
# ==========================================
@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') == 'siswa':
        return render_template('dashboard_siswa.html')  # Sesuai dengan file yang ada di direktori
    return redirect(url_for('login'))

@app.route('/user/buku')
def user_buku():
    if session.get('role') == 'siswa':
        return render_template('user/buku.html')
    return redirect(url_for('login'))

@app.route('/user/peminjaman')
def user_peminjaman():
    if session.get('role') == 'siswa':
        return render_template('user/peminjaman.html')
    return redirect(url_for('login'))

@app.route('/user/riwayat')
def user_riwayat():
    if session.get('role') == 'siswa':
        return render_template('user/riwayat.html')
    return redirect(url_for('login'))

@app.route('/user/biodata')
def user_biodata():
    if session.get('role') == 'siswa':
        return render_template('user/biodata.html')
    return redirect(url_for('login'))


# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)