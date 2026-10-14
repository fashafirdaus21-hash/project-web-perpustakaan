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
# FITUR CRUD BUKU (ADMIN)
# ==========================================

# 1. READ: Menampilkan Daftar Buku (Halaman Kelola Buku)
@app.route('/admin/buku')
def kelola_buku():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # Mengambil data buku sekaligus menggabungkannya (JOIN) dengan nama kategori
  query = """
        SELECT buku.*, kategori.nama_kategori 
        FROM buku 
        JOIN kategori ON buku.id_kategori = kategori.id_kategori
    """
  cursor.execute(query)
  daftar_buku = cursor.fetchall()

  cursor.close()
  conn.close()

  # Untuk sementara, kita tampilkan dalam bentuk teks terstruktur / JSON sederhana di browser
  # Nanti bisa diganti dengan render_template('admin_buku.html', buku=daftar_buku) jika frontend sudah siap
  return {'status': 'success', 'data_buku': daftar_buku}


# 2. CREATE: Menambah Buku Baru (Menerima input POST dari form tambah buku)
@app.route('/admin/buku/tambah', methods=['POST'])
def tambah_buku():
  judul = request.form['judul']
  penulis = request.form['penulis']
  id_kategori = request.form['id_kategori']
  tahun_terbit = request.form['tahun_terbit']
  jumlah_total = int(request.form['jumlah_total'])

  # Saat buku baru ditambahkan, jumlah tersedia otomatis sama dengan jumlah total
  jumlah_tersedia = jumlah_total

  conn = get_db_connection()
  cursor = conn.cursor()

  query = """
        INSERT INTO buku (judul, penulis, id_kategori, tahun_terbit, jumlah_total, jumlah_tersedia) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
  cursor.execute(
      query,
      (judul, penulis, id_kategori, tahun_terbit, jumlah_total, jumlah_tersedia),
  )
  conn.commit()

  cursor.close()
  conn.close()

  return 'Buku berhasil ditambahkan! <a href="/admin/buku">Lihat Data Buku</a>'


# 3. DELETE: Menghapus Buku Berdasarkan ID
@app.route('/admin/buku/hapus/<int:id_buku>', methods=['POST', 'GET'])
def hapus_buku(id_buku):
  conn = get_db_connection()
  cursor = conn.cursor()

  try:
    query = 'DELETE FROM buku WHERE id_buku = %s'
    cursor.execute(query, (id_buku,))
    conn.commit()
    pesan = 'Buku berhasil dihapus!'
  except mysql.connector.Error as err:
    pesan = (
        'Gagal menghapus buku (kemungkinan buku sedang dipinjam):'
        f' {err.msg}'
    )
  finally:
    cursor.close()
    conn.close()

  return f'{pesan} <a href="/admin/buku">Kembali ke Kelola Buku</a>'



# ==========================================
# FITUR PEMINJAMAN BUKU (ADMIN / TRANSAKSI)
# ==========================================

# 1. READ: Menampilkan Daftar Peminjaman
@app.route('/admin/peminjaman')
def daftar_peminjaman():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # Menggabungkan data peminjaman dengan data anggota dan buku agar nama & judulnya muncul
  query = """
        SELECT peminjaman.*, anggota.nama_lengkap, buku.judul 
        FROM peminjaman 
        JOIN anggota ON peminjaman.id_anggota = anggota.id_anggota 
        JOIN buku ON peminjaman.id_buku = buku.id_buku
    """
  cursor.execute(query)
  hasil_peminjaman = cursor.fetchall()

  cursor.close()
  conn.close()

  return {'status': 'success', 'data_peminjaman': hasil_peminjaman}


# 2. CREATE: Proses Input Peminjaman Baru (Mengurangi Stok Buku Otomatis)
@app.route('/admin/peminjaman/tambah', methods=['POST'])
def tambah_peminjaman():
  id_anggota = request.form['id_anggota']
  id_buku = request.form['id_buku']
  tanggal_pinjam = request.form['tanggal_pinjam']
  tanggal_jatuh_tempo = request.form['tanggal_jatuh_tempo']

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # Cek terlebih dahulu apakah stok buku masih ada
  cursor.execute('SELECT jumlah_tersedia FROM buku WHERE id_buku = %s', (id_buku,))
  buku = cursor.fetchone()

  if buku and buku['jumlah_tersedia'] > 0:
    try:
      # Menggunakan transaksi agar jika ada error, perubahan dibatalkan (rollback)
      conn.start_transaction()

      # Masukkan data ke tabel peminjaman
      query_pinjam = """
                INSERT INTO peminjaman (id_anggota, id_buku, tanggal_pinjam, tanggal_jatuh_tempo, status) 
                VALUES (%s, %s, %s, %s, 'dipinjam')
            """
      cursor.execute(
          query_pinjam,
          (id_anggota, id_buku, tanggal_pinjam, tanggal_jatuh_tempo),
      )

      # Kurangi jumlah_tersedia di tabel buku sejumlah 1
      query_update_buku = (
          'UPDATE buku SET jumlah_tersedia = jumlah_tersedia - 1 WHERE id_buku'
          ' = %s'
      )
      cursor.execute(query_update_buku, (id_buku,))

      conn.commit()
      pesan = (
          'Transaksi peminjaman berhasil disimpan dan stok buku berkurang!'
      )
    except Exception as e:
      conn.rollback()
      pesan = f'Gagal memproses peminjaman karena error: {e}'
  else:
    pesan = 'Gagal: Buku tidak ditemukan atau stok buku sedang kosong (0)!'

  cursor.close()
  conn.close()

  return f'{pesan} <a href="/admin/peminjaman">Lihat Data Peminjaman</a>'



# ==========================================
# FITUR PENGEMBALIAN BUKU & KALKULASI DENDA
# ==========================================

# 1. READ: Menampilkan Daftar Pengembalian
@app.route('/admin/pengembalian')
def daftar_pengembalian():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  query = """
        SELECT pengembalian.*, peminjaman.id_anggota, peminjaman.id_buku, buku.judul 
        FROM pengembalian 
        JOIN peminjaman ON pengembalian.id_peminjaman = peminjaman.id_peminjaman
        JOIN buku ON peminjaman.id_buku = buku.id_buku
    """
  cursor.execute(query)
  hasil_pengembalian = cursor.fetchall()

  cursor.close()
  conn.close()

  return {'status': 'success', 'data_pengembalian': hasil_pengembalian}


# 2. CREATE: Proses Pengembalian Buku & Hitung Denda Otomatis
@app.route('/admin/pengembalian/tambah', methods=['POST'])
def proses_pengembalian():
  id_peminjaman = request.form['id_peminjaman']
  tanggal_kembali_str = request.form[
      'tanggal_kembali'
  ]  # Format: 'YYYY-MM-DD'
  kondisi_buku = request.form[
      'kondisi_buku'
  ]  # 'Baik', 'Rusak Ringan', 'Rusak Berat'

  from datetime import datetime

  tanggal_kembali = datetime.strptime(tanggal_kembali_str, '%Y-%m-%d').date()

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # Cek apakah data peminjaman dengan status 'dipinjam' benar-benar ada
  cursor.execute(
      "SELECT * FROM peminjaman WHERE id_peminjaman = %s AND status = 'dipinjam'",
      (id_peminjaman,),
  )
  peminjaman = cursor.fetchone()

  if not peminjaman:
    cursor.close()
    conn.close()
    return (
        'Gagal: Data peminjaman tidak ditemukan atau buku sudah dikembalikan'
        ' sebelumnya! <a href="/admin/pengembalian">Kembali</a>'
    )

  tanggal_jatuh_tempo = peminjaman['tanggal_jatuh_tempo']
  id_buku = peminjaman['id_buku']

  # Ambil parameter denda dari tabel pengaturan database
  cursor.execute('SELECT * FROM pengaturan')
  pengaturan_rows = cursor.fetchall()

  # Nilai default jika parameter di database belum diset
  tarif_denda_telat = 1000
  tarif_rusak_ringan = 10000
  tarif_rusak_berat = 50000

  for p in pengaturan_rows:
    if p['param_key'] == 'tarif_denda_per_hari':
      tarif_denda_telat = int(p['param_value'])
    elif p['param_key'] == 'tarif_rusak_ringan':
      tarif_rusak_ringan = int(p['param_value'])
    elif p['param_key'] == 'tarif_rusak_berat':
      tarif_rusak_berat = int(p['param_value'])

  # Kalkulasi denda keterlambatan hari
  denda_telat = 0
  if tanggal_kembali > tanggal_jatuh_tempo:
    selisih_hari = (tanggal_kembali - tanggal_jatuh_tempo).days
    denda_telat = selisih_hari * tarif_denda_telat

  # Kalkulasi denda berdasarkan kondisi fisik buku
  denda_kondisi = 0
  if kondisi_buku == 'Rusak Ringan':
    denda_kondisi = tarif_rusak_ringan
  elif kondisi_buku == 'Rusak Berat':
    denda_kondisi = tarif_rusak_berat

  total_denda = denda_telat + denda_kondisi

  try:
    conn.start_transaction()

    # 1. Masukkan data ke tabel pengembalian
    query_pengembalian = """
            INSERT INTO pengembalian (id_peminjaman, tanggal_kembali, denda, kondisi_buku) 
            VALUES (%s, %s, %s, %s)
        """
    cursor.execute(
        query_pengembalian,
        (id_peminjaman, tanggal_kembali_str, total_denda, kondisi_buku),
    )

    # 2. Ubah status peminjaman menjadi 'dikembalikan'
    cursor.execute(
        "UPDATE peminjaman SET status = 'dikembalikan' WHERE id_peminjaman = %s",
        (id_peminjaman,),
    )

    # 3. Kembalikan stok buku yang tersedia (+ 1)
    cursor.execute(
        'UPDATE buku SET jumlah_tersedia = jumlah_tersedia + 1 WHERE id_buku ='
        ' %s',
        (id_buku,),
    )

    conn.commit()
    pesan = f'Pengembalian berhasil diproses! Total Denda: Rp {total_denda:,}'
  except Exception as e:
    conn.rollback()
    pesan = f'Gagal memproses pengembalian: {e}'

  cursor.close()
  conn.close()

  return f'{pesan} <a href="/admin/pengembalian">Lihat Data Pengembalian</a>'




# Rute API Analitik untuk Laporan Kepala Sekolah
@app.route('/api/laporan/statistik')
def statistik_kepsek():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # 1. Rekap kondisi buku untuk grafik persentase
  cursor.execute(
      'SELECT kondisi_buku, COUNT(*) as total FROM pengembalian GROUP BY'
      ' kondisi_buku'
  )
  kondisi_buku = cursor.fetchall()

  # 2. Total ringkasan peminjaman keseluruhan
  cursor.execute('SELECT COUNT(*) as total_peminjaman FROM peminjaman')
  total_pinjam = cursor.fetchone()

  cursor.close()
  conn.close()

  return {
      'status': 'success',
      'statistik_kondisi': kondisi_buku,
      'ringkasan': total_pinjam,
  }


# ==========================================
# FITUR LAPORAN & ANALITIK (KEPSEK & ADMIN)
# ==========================================

# 1. Laporan Transaksi Lengkap (Mendukung Pencarian Nama/Judul & Filter Status)
@app.route('/admin/laporan/transaksi')
def laporan_transaksi():
  # Menangkap parameter pencarian opsional dari URL (contoh: /admin/laporan/transaksi?q=budi&status=selesai)
  keyword = request.args.get('q', '')
  status = request.args.get('status', '')

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

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

  search_pattern = f'%{keyword}%'
  params = [search_pattern, search_pattern]

  if status:
    query += ' AND peminjaman.status = %s'
    params.append(status)

  query += ' ORDER BY peminjaman.tanggal_pinjam DESC'

  cursor.execute(query, params)
  data_laporan = cursor.fetchall()

  cursor.close()
  conn.close()

  return {'status': 'success', 'laporan_transaksi': data_laporan}


# 2. Analitik & Rekap Data (Grafik Peminjaman per Bulan & Kondisi Buku)
@app.route('/admin/laporan/analitik')
def analitik_kepsek():
  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True)

  # A. Statistik Peminjaman per Bulan (untuk rekap grafik bulanan)
  cursor.execute("""
        SELECT DATE_FORMAT(tanggal_pinjam, '%Y-%m') AS bulan, COUNT(*) AS total_peminjaman
        FROM peminjaman
        GROUP BY bulan
        ORDER BY bulan ASC
    """)
  peminjaman_per_bulan = cursor.fetchall()

  # B. Statistik Kondisi Buku saat Pengembalian (Persentase Baik / Rusak)
  cursor.execute("""
        SELECT kondisi_buku, COUNT(*) AS total
        FROM pengembalian
        WHERE kondisi_buku IS NOT NULL
        GROUP BY kondisi_buku
    """)
  kondisi_buku = cursor.fetchall()

  # C. Ringkasan Total Keseluruhan
  cursor.execute('SELECT COUNT(*) AS total_buku FROM buku')
  total_buku = cursor.fetchone()['total_buku']

  cursor.execute('SELECT COUNT(*) AS total_peminjaman FROM peminjaman')
  total_peminjaman = cursor.fetchone()['total_peminjaman']

  cursor.close()
  conn.close()

  return {
      'status': 'success',
      'peminjaman_per_bulan': peminjaman_per_bulan,
      'kondisi_buku': kondisi_buku,
      'ringkasan': {
          'total_buku': total_buku,
          'total_peminjaman': total_peminjaman,
      },
  }



# ==========================================
# BAGIAN PALING BAWAH: MENJALANKAN SERVER
# ==========================================
if __name__ == "__main__":
  app.run(debug=True)