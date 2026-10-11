import mysql.connector

try:
    # 1. Menghubungkan Python ke Database MySQL di XAMPP
    db = mysql.connector.connect(
        host="localhost",           # Karena server database ada di laptopmu sendiri
        user="root",                # Username default XAMPP
        password="",                # Password default XAMPP (dikosongkan)
        database="db_perpustakaan"  # Nama database yang sudah kamu buat
    )

    if db.is_connected():
        print("Berhasil terhubung ke database perpustakaan!")

        # 2. Membuat kursor (alat pembawa perintah SQL)
        cursor = db.cursor()

        # 3. Menjalankan perintah SQL untuk mengambil data buku
        cursor.execute("SELECT * FROM buku")
        
        # 4. Menangkap hasil data dari database
        daftar_buku = cursor.fetchall()

        print("\nDaftar Buku di Perpustakaan:")
        for buku in daftar_buku:
            # Mengakses kolom berdasarkan urutan (0: id, 1: judul, 2: pengarang, dst.)
            print(f"- ID: {buku[0]} | Judul: {buku[1]} | Pengarang: {buku[2]} | Stok: {buku[5]}")

except Exception as e:
    print(f"Gagal terhubung ke database: {e}")

finally:
    # 5. Menutup koneksi database dengan aman setelah selesai
    if 'db' in locals() and db.is_connected():
        db.close()
        print("\nKoneksi database ditutup.")