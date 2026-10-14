from datetime import datetime
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
# 1. HALAMAN UTAMA & LOGIN
# ==========================================
@app.route("/")
def login_page():
  return render_template("login.html")


@app.route("/login", methods=["POST"])
def proses_login():
  id_user = request.form["id_user"]
  password = request.form["password"]

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  try:
    cursor.execute("SELECT * FROM users WHERE id_user = %s", (id_user,))
    user = cursor.fetchone()
  except Exception:
    user = None

  cursor.close()
  conn.close()

  if user:
    role = user["role"]
    if role == "admin":
      return redirect(url_for("dashboard_admin"))
    elif role == "siswa":
      return redirect(url_for("dashboard_siswa", id_user=user["id_user"]))
    elif role == "kepsek":
      return redirect(url_for("dashboard_kepsek"))
    else:
      return redirect(url_for("dashboard_siswa", id_user=user["id_user"]))
  else:
    # Mode fleksibel untuk pengujian UI dashboard langsung
    return redirect(url_for("dashboard_siswa", id_user=id_user))


# ==========================================
# 2. DASHBOARD SISWA (TERINTEGRASI HTML TEMAN)
# ==========================================
@app.route("/dashboard/siswa/<id_user>")
def dashboard_siswa(id_user):
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # A. Ambil Biodata Siswa
  try:
    cursor.execute("SELECT * FROM anggota WHERE id_anggota = %s", (id_user,))
    biodata = cursor.fetchone()
  except Exception:
    biodata = None

  if not biodata:
    biodata = {
        "id_anggota": id_user,
        "nama_lengkap": "USER KELAS",
        "kelas": "XII IPA",
        "status_keanggotaan": "Aktif",
        "kategori": "Mahasiswa Reguler",
    }

  # B. Ambil Daftar Buku
  try:
    query_buku = """
            SELECT buku.*, kategori.nama_kategori 
            FROM buku 
            LEFT JOIN kategori ON buku.id_kategori = kategori.id_kategori
        """
    cursor.execute(query_buku)
    daftar_buku = cursor.fetchall()
  except Exception:
    daftar_buku = []

  # C. Statistik Real-time
  try:
    cursor.execute(
        "SELECT COUNT(*) AS total FROM peminjaman WHERE id_anggota = %s AND"
        " status = 'dipinjam'",
        (id_user,),
    )
    sedang_dipinjam = cursor.fetchone()["total"]
  except Exception:
    sedang_dipinjam = 0

  try:
    cursor.execute(
        "SELECT COUNT(*) AS total FROM peminjaman WHERE id_anggota = %s AND"
        " status = 'pending'",
        (id_user,),
    )
    menunggu_acc = cursor.fetchone()["total"]
  except Exception:
    menunggu_acc = 0

  total_denda = 0
  try:
    query_denda = """
            SELECT COALESCE(SUM(pengembalian.denda), 0) AS total_denda
            FROM pengembalian 
            JOIN peminjaman ON pengembalian.id_peminjaman = peminjaman.id_peminjaman
            WHERE peminjaman.id_anggota = %s
        """
    cursor.execute(query_denda, (id_user,))
    res_denda = cursor.fetchone()
    if res_denda:
      total_denda = res_denda["total_denda"]
  except Exception:
    total_denda = 0

  # D. Riwayat Peminjaman
  try:
    query_peminjaman = """
            SELECT peminjaman.*, buku.judul 
            FROM peminjaman 
            JOIN buku ON peminjaman.id_buku = buku.id_buku
            WHERE peminjaman.id_anggota = %s
            ORDER BY peminjaman.tanggal_pinjam DESC
        """
    cursor.execute(query_peminjaman, (id_user,))
    riwayat_peminjaman = cursor.fetchall()
  except Exception:
    riwayat_peminjaman = []

  cursor.close()
  conn.close()

  stat = {
      "sedang_dipinjam": sedang_dipinjam,
      "menunggu_acc": menunggu_acc,
      "total_denda": total_denda,
  }

  return render_template(
      "dashboard_siswa.html",
      biodata=biodata,
      daftar_buku=daftar_buku,
      stat=stat,
      riwayat_peminjaman=riwayat_peminjaman,
  )


# ==========================================
# 3. DASHBOARD ADMIN & KEPSEK
# ==========================================
@app.route("/dashboard/admin")
def dashboard_admin():
  return "Ini adalah Halaman Dashboard Admin"


@app.route("/dashboard/kepsek")
def dashboard_kepsek():
  return "Ini adalah Halaman Ringkasan Kepala Sekolah"


# ==========================================
# 4. FITUR CRUD BUKU (ADMIN)
# ==========================================
@app.route("/admin/buku")
def kelola_buku():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  try:
    query = """
            SELECT buku.*, kategori.nama_kategori 
            FROM buku 
            JOIN kategori ON buku.id_kategori = kategori.id_kategori
        """
    cursor.execute(query)
    daftar_buku = cursor.fetchall()
  except Exception:
    daftar_buku = []
  cursor.close()
  conn.close()
  return {"status": "success", "data_buku": daftar_buku}


@app.route("/admin/buku/tambah", methods=["POST"])
def tambah_buku():
  judul = request.form["judul"]
  penulis = request.form["penulis"]
  id_kategori = request.form["id_kategori"]
  tahun_terbit = request.form["tahun_terbit"]
  jumlah_total = int(request.form["jumlah_total"])
  jumlah_tersedia = jumlah_total

  conn = get_db_connection()
  cursor = conn.cursor()
  query = """
        INSERT INTO buku (judul, penulis, id_kategori, tahun_terbit, jumlah_total, jumlah_tersedia) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
  cursor.execute(
      query,
      (
          judul,
          penulis,
          id_kategori,
          tahun_terbit,
          jumlah_total,
          jumlah_tersedia,
      ),
  )
  conn.commit()
  cursor.close()
  conn.close()
  return 'Buku berhasil ditambahkan! <a href="/admin/buku">Lihat Data Buku</a>'


@app.route("/admin/buku/hapus/<int:id_buku>", methods=["POST", "GET"])
def hapus_buku(id_buku):
  conn = get_db_connection()
  cursor = conn.cursor()
  try:
    query = "DELETE FROM buku WHERE id_buku = %s"
    cursor.execute(query, (id_buku,))
    conn.commit()
    pesan = "Buku berhasil dihapus!"
  except mysql.connector.Error as err:
    pesan = f"Gagal menghapus buku: {err.msg}"
  finally:
    cursor.close()
    conn.close()
  return f'{pesan} <a href="/admin/buku">Kembali ke Kelola Buku</a>'


# ==========================================
# 5. FITUR PEMINJAMAN BUKU
# ==========================================
@app.route("/admin/peminjaman")
def daftar_peminjaman():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  try:
    query = """
            SELECT peminjaman.*, anggota.nama_lengkap, buku.judul 
            FROM peminjaman 
            JOIN anggota ON peminjaman.id_anggota = anggota.id_anggota 
            JOIN buku ON peminjaman.id_buku = buku.id_buku
        """
    cursor.execute(query)
    hasil_peminjaman = cursor.fetchall()
  except Exception:
    hasil_peminjaman = []
  cursor.close()
  conn.close()
  return {"status": "success", "data_peminjaman": hasil_peminjaman}


@app.route("/admin/peminjaman/tambah", methods=["POST"])
def tambah_peminjaman():
  id_anggota = request.form["id_anggota"]
  id_buku = request.form["id_buku"]
  tanggal_pinjam = request.form["tanggal_pinjam"]
  tanggal_jatuh_tempo = request.form["tanggal_jatuh_tempo"]

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  cursor.execute(
      "SELECT jumlah_tersedia FROM buku WHERE id_buku = %s", (id_buku,)
  )
  buku = cursor.fetchone()

  if buku and buku["jumlah_tersedia"] > 0:
    try:
      conn.start_transaction()
      query_pinjam = """
                INSERT INTO peminjaman (id_anggota, id_buku, tanggal_pinjam, tanggal_jatuh_tempo, status) 
                VALUES (%s, %s, %s, %s, 'dipinjam')
            """
      cursor.execute(
          query_pinjam,
          (id_anggota, id_buku, tanggal_pinjam, tanggal_jatuh_tempo),
      )
      query_update_buku = (
          "UPDATE buku SET jumlah_tersedia = jumlah_tersedia - 1 WHERE id_buku"
          " = %s"
      )
      cursor.execute(query_update_buku, (id_buku,))
      conn.commit()
      pesan = "Transaksi peminjaman berhasil disimpan dan stok buku berkurang!"
    except Exception as e:
      conn.rollback()
      pesan = f"Gagal memproses peminjaman: {e}"
  else:
    pesan = "Gagal: Buku tidak ditemukan atau stok buku kosong!"

  cursor.close()
  conn.close()
  return f'{pesan} <a href="/admin/peminjaman">Lihat Data Peminjaman</a>'


# ==========================================
# 6. FITUR PENGEMBALIAN BUKU & DENDA
# ==========================================
@app.route("/admin/pengembalian")
def daftar_pengembalian():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  try:
    query = """
            SELECT pengembalian.*, peminjaman.id_anggota, peminjaman.id_buku, buku.judul 
            FROM pengembalian 
            JOIN peminjaman ON pengembalian.id_peminjaman = peminjaman.id_peminjaman
            JOIN buku ON peminjaman.id_buku = buku.id_buku
        """
    cursor.execute(query)
    hasil_pengembalian = cursor.fetchall()
  except Exception:
    hasil_pengembalian = []
  cursor.close()
  conn.close()
  return {"status": "success", "data_pengembalian": hasil_pengembalian}


@app.route("/admin/pengembalian/tambah", methods=["POST"])
def proses_pengembalian():
  id_peminjaman = request.form["id_peminjaman"]
  tanggal_kembali_str = request.form["tanggal_kembali"]
  kondisi_buku = request.form["kondisi_buku"]

  tanggal_kembali = datetime.strptime(tanggal_kembali_str, "%Y-%m-%d").date()

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  cursor.execute(
      "SELECT * FROM peminjaman WHERE id_peminjaman = %s AND status = 'dipinjam'",
      (id_peminjaman,),
  )
  peminjaman = cursor.fetchone()

  if not peminjaman:
    cursor.close()
    conn.close()
    return (
        "Gagal: Data peminjaman tidak ditemukan! <a"
        ' href="/admin/pengembalian">Kembali</a>'
    )

  tanggal_jatuh_tempo = peminjaman["tanggal_jatuh_tempo"]
  id_buku = peminjaman["id_buku"]

  try:
    cursor.execute("SELECT * FROM pengaturan")
    pengaturan_rows = cursor.fetchall()
  except Exception:
    pengaturan_rows = []

  tarif_denda_telat = 1000
  tarif_rusak_ringan = 10000
  tarif_rusak_berat = 50000

  for p in pengaturan_rows:
    if p["param_key"] == "tarif_denda_per_hari":
      tarif_denda_telat = int(p["param_value"])
    elif p["param_key"] == "tarif_rusak_ringan":
      tarif_rusak_ringan = int(p["param_value"])
    elif p["param_key"] == "tarif_rusak_berat":
      tarif_rusak_berat = int(p["param_value"])

  denda_telat = 0
  if tanggal_kembali > tanggal_jatuh_tempo:
    selisih_hari = (tanggal_kembali - tanggal_jatuh_tempo).days
    denda_telat = selisih_hari * tarif_denda_telat

  denda_kondisi = 0
  if kondisi_buku == "Rusak Ringan":
    denda_kondisi = tarif_rusak_ringan
  elif kondisi_buku == "Rusak Berat":
    denda_kondisi = tarif_rusak_berat

  total_denda = denda_telat + denda_kondisi

  try:
    conn.start_transaction()
    query_pengembalian = """
            INSERT INTO pengembalian (id_peminjaman, tanggal_kembali, denda, kondisi_buku) 
            VALUES (%s, %s, %s, %s)
        """
    cursor.execute(
        query_pengembalian,
        (id_peminjaman, tanggal_kembali_str, total_denda, kondisi_buku),
    )
    cursor.execute(
        "UPDATE peminjaman SET status = 'dikembalikan' WHERE id_peminjaman = %s",
        (id_peminjaman,),
    )
    cursor.execute(
        "UPDATE buku SET jumlah_tersedia = jumlah_tersedia + 1 WHERE id_buku ="
        " %s",
        (id_buku,),
    )
    conn.commit()
    pesan = f"Pengembalian berhasil diproses! Total Denda: Rp {total_denda:,}"
  except Exception as e:
    conn.rollback()
    pesan = f"Gagal memproses pengembalian: {e}"

  cursor.close()
  conn.close()
  return f'{pesan} <a href="/admin/pengembalian">Lihat Data Pengembalian</a>'


# ==========================================
# 7. LAPORAN & ANALITIK KEPSEK/ADMIN
# ==========================================
@app.route("/admin/laporan/transaksi")
def laporan_transaksi():
  keyword = request.args.get("q", "")
  status = request.args.get("status", "")

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  try:
    query = """
            SELECT peminjaman.id_peminjaman, peminjaman.tanggal_pinjam, peminjaman.tanggal_jatuh_tempo, 
                   peminjaman.status, anggota.nama_lengkap, buku.judul, 
                   pengembalian.tanggal_kembali, pengembalian.denda, pengembalian.kondisi_buku
            FROM peminjaman 
            JOIN anggota ON peminjaman.id_anggota = anggota.id_anggota 
            JOIN buku ON peminjaman.id_buku = buku.id_buku
            LEFT JOIN pengembalian ON peminjaman.id_peminjaman = pengembalian.id_peminjaman
            WHERE (anggota.nama_lengkap LIKE %s OR buku.judul LIKE %s)
        """
    search_pattern = f"%{keyword}%"
    params = [search_pattern, search_pattern]

    if status:
      query += " AND peminjaman.status = %s"
      params.append(status)

    query += " ORDER BY peminjaman.tanggal_pinjam DESC"
    cursor.execute(query, params)
    data_laporan = cursor.fetchall()
  except Exception:
    data_laporan = []
  cursor.close()
  conn.close()
  return {"status": "success", "laporan_transaksi": data_laporan}


@app.route("/admin/laporan/analitik")
def analitik_kepsek():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)
  try:
    cursor.execute("""
            SELECT DATE_FORMAT(tanggal_pinjam, '%Y-%m') AS bulan, COUNT(*) AS total_peminjaman
            FROM peminjaman
            GROUP BY bulan
            ORDER BY bulan ASC
        """)
    peminjaman_per_bulan = cursor.fetchall()

    cursor.execute("""
            SELECT kondisi_buku, COUNT(*) AS total
            FROM pengembalian
            WHERE kondisi_buku IS NOT NULL
            GROUP BY kondisi_buku
        """)
    kondisi_buku = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total_buku FROM buku")
    total_buku = cursor.fetchone()["total_buku"]

    cursor.execute("SELECT COUNT(*) AS total_peminjaman FROM peminjaman")
    total_peminjaman = cursor.fetchone()["total_peminjaman"]
  except Exception:
    peminjaman_per_bulan = []
    kondisi_buku = []
    total_buku = 0
    total_peminjaman = 0

  cursor.close()
  conn.close()
  return {
      "status": "success",
      "peminjaman_per_bulan": peminjaman_per_bulan,
      "kondisi_buku": kondisi_buku,
      "ringkasan": {
          "total_buku": total_buku,
          "total_peminjaman": total_peminjaman,
      },
  }


if __name__ == "__main__":
  app.run(debug=True)