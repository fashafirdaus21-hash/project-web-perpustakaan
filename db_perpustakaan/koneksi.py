import mysql.connector

def koneksi_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Kosongkan jika XAMPP default tidak pakai password
            database="db_perpustakaan"
        )
        return db
    except Exception as e:
        print(f"Koneksi database gagal: {e}")
        return None