from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)


# Fungsi untuk menghubungkan ke database
def get_db_connection():
  return mysql.connector.connect(
      host="localhost",
      user="root",
      password="",
      database="db_perpustakaan",
  )


# Rute Halaman Login (Tampilan awal saat web dibuka)
@app.route("/")
def index():
  return render_template(
      "login.html"
  )  # Memanggil file HTML login yang akan kita buat


if __name__ == "__main__":
  app.run(debug=True)