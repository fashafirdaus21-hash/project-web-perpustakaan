-- =========================================================
-- DATABASE PERPUSTAKAAN SEKOLAH DENGAN MULTI-ROLE
-- =========================================================

CREATE DATABASE IF NOT EXISTS db_perpustakaan;
USE db_perpustakaan;

-- 1. TABEL KATEGORI BUKU
CREATE TABLE kategori (
    id_kategori INT AUTO_INCREMENT PRIMARY KEY,
    nama_kategori VARCHAR(50) NOT NULL
);

-- 2. TABEL BUKU
CREATE TABLE buku (
    id_buku INT AUTO_INCREMENT PRIMARY KEY,
    judul VARCHAR(150) NOT NULL,
    pengarang VARCHAR(100) NOT NULL,
    penerbit VARCHAR(100),
    tahun_terbit INT,
    stok INT DEFAULT 0,
    id_kategori INT,
    FOREIGN KEY (id_kategori) REFERENCES kategori(id_kategori) ON DELETE SET NULL
);

-- 3. TABEL ANGGOTA (DATA PROFIL SISWA)
CREATE TABLE anggota (
    id_anggota INT AUTO_INCREMENT PRIMARY KEY,
    nis VARCHAR(20) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL,
    kelas VARCHAR(20) NOT NULL,
    no_hp VARCHAR(15)
);

-- 4. TABEL PENGGUNA (AKUN LOGIN & HAK AKSES ROLE)
CREATE TABLE pengguna (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('murid', 'admin', 'kepala_sekolah') NOT NULL,
    id_anggota INT NULL, -- Hanya terisi jika role = 'murid'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_anggota) REFERENCES anggota(id_anggota) ON DELETE CASCADE
);

-- 5. TABEL PEMINJAMAN (TRANSAKSI)
CREATE TABLE peminjaman (
    id_peminjaman INT AUTO_INCREMENT PRIMARY KEY,
    id_anggota INT NOT NULL,
    tgl_pinjam DATE NOT NULL,
    tgl_jatuh_tempo DATE NOT NULL,
    status ENUM('dipinjam', 'kembali', 'terlambat') DEFAULT 'dipinjam',
    FOREIGN KEY (id_anggota) REFERENCES anggota(id_anggota) ON DELETE CASCADE
);

-- 6. TABEL DETAIL PEMINJAMAN
CREATE TABLE detail_peminjaman (
    id_detail INT AUTO_INCREMENT PRIMARY KEY,
    id_peminjaman INT NOT NULL,
    id_buku INT NOT NULL,
    denda INT DEFAULT 0,
    FOREIGN KEY (id_peminjaman) REFERENCES peminjaman(id_peminjaman) ON DELETE CASCADE,
    FOREIGN KEY (id_buku) REFERENCES buku(id_buku) ON DELETE CASCADE
);

-- =========================================================
-- DATA DUMMY UNTUK UJI COBA
-- =========================================================

-- Data Kategori
INSERT INTO kategori (nama_kategori) VALUES 
('Fiksi'), 
('Sains'), 
('Sejarah');

-- Data Buku
INSERT INTO buku (judul, pengarang, penerbit, tahun_terbit, stok, id_kategori) VALUES
('Laskar Pelangi', 'Andrea Hirata', 'Bentang Pustaka', 2005, 5, 1),
('Fisika Dasar', 'Halliday & Resnick', 'Erlangga', 2014, 3, 2),
('Sejarah Indonesia Modern', 'M.C. Ricklefs', 'Serambi', 2008, 2, 3);

-- Data Anggota (Siswa)
INSERT INTO anggota (nis, nama, kelas, no_hp) VALUES
('1001', 'Budi Santoso', 'X-IPA-1', '081234567890'),
('1002', 'Siti Rahma', 'XI-IPS-2', '089876543210');

-- Data Akun Pengguna (Login)
INSERT INTO pengguna (username, password, role, id_anggota) VALUES
('admin_perpus', 'admin123', 'admin', NULL),
('kepala_sekolah', 'kepsek123', 'kepala_sekolah', NULL),
('budi1001', 'siswa123', 'murid', 1),
('siti1002', 'siswa123', 'murid', 2);

-- Data Transaksi Peminjaman
INSERT INTO peminjaman (id_anggota, tgl_pinjam, tgl_jatuh_tempo, status) VALUES
(1, '2026-10-01', '2026-10-08', 'dipinjam');

-- Detail Peminjaman Buku
INSERT INTO detail_peminjaman (id_peminjaman, id_buku, denda) VALUES
(1, 1, 0);