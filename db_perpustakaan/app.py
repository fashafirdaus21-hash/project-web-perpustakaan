# ==========================================
# BAGIAN ATAS: PUSTAKA & KONEKSI DATABASE
# ==========================================
from flask import Flask, redirect, render_template, request, url_for
import mysql.connector

app = Flask(__name__)


def get_db_connection():
  return mysql.connector.connect(
      host="localhost",
      user="root",
      password="",
      database="db_perpustakaan",
  )


# ==========================================
# BAGIAN TENGAH: RUTE / HALAMAN WEBSITE
# ==========================================

# 1. Menampilkan Halaman Login
@app.route("/")
def login_page():
  return render_template("login.html")


# 2. Memproses Logika Saat Tombol Masuk Ditekan
@app.route("/login", methods=["POST"])
def proses_login():
  id_user = request.form["id_user"]
  password = request.form["password"]

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  query = "SELECT * FROM users WHERE id_user = %s AND is_active = 1"
  cursor.execute(query, (id_user,))
  user = cursor.fetchone()

  cursor.close()
  conn.close()

  if user:
    if user["password_hash"] == password:
      role = user["role"]

      # Pengarahan Berdasarkan Role
      if role == "admin":
        return redirect(url_for("dashboard_admin"))
      elif role == "siswa":
        return redirect(url_for("dashboard_siswa", id_user=user["id_user"]))
      elif role == "kepsek":
        return redirect(url_for("dashboard_kepsek"))
      elif role == "programmer":
        return "Berhasil Login sebagai Programmer/Super Admin"
    else:
      return "Kata sandi salah! <a href='/'>Coba lagi</a>"
  else:
    return (
        "ID Pengguna tidak ditemukan atau akun dinonaktifkan! <a"
        " href='/'>Coba lagi</a>"
    )


# 3. Halaman-halaman Dashboard Tujuan
@app.route("/dashboard/siswa/<id_user>")
def dashboard_siswa(id_user):
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  cursor.execute("SELECT * FROM anggota WHERE id_anggota = %s", (id_user,))
  biodata = cursor.fetchone()
  cursor.close()
  conn.close()

  return (
      f"Selamat Datang di Dashboard Siswa, {biodata['nama_lengkap']}! (Kelas:"
      f" {biodata['kelas']}, Kategori: {biodata['kategori']})"
  )


@app.route("/dashboard/admin")
def dashboard_admin():
  return "Ini adalah Halaman Dashboard Admin"


@app.route("/dashboard/kepsek")
def dashboard_kepsek():
  return "Ini adalah Halaman Ringkasan Kepala Sekolah"


# ==========================================
# BAGIAN PALING BAWAH: MENJALANKAN SERVER
# ==========================================
if __name__ == "__main__":
  app.run(debug=True)