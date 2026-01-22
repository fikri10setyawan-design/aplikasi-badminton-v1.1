import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- SISTEM LOGIN ---
# 1. Siapkan "Ingatan" untuk menyimpan status login
if 'sudah_login' not in st.session_state:
    st.session_state['sudah_login'] = False
    st.session_state['user_role'] = ""

# --- LOGIKA MEMBERSIHKAN FORM (VERSI BARU) ---
if 'bersihkan_form' not in st.session_state:
    st.session_state['bersihkan_form'] = False

if st.session_state['bersihkan_form']:
    st.session_state["input_member"] = ""
    if st.session_state['user_role'] == "Member":
        st.session_state["input_nominal"] = 20000 # Member otomatis 20rb
    else:
        st.session_state["input_nominal"] = 0     # Admin mulai dari 0
    # ---------------------------
    
    st.session_state["input_ket"] = ""
    st.session_state['bersihkan_form'] = False

# --- FUNGSI MEMBERSIHKAN FORM ---
def clear_form():
    st.session_state["input_member"] = ""
    st.session_state["input_nominal"] = 0
    st.session_state["input_ket"] = ""
    # Tanggal, Jenis, dan Kategori biasanya tidak perlu di-reset

# 2. Fungsi Form Login
def login_form():
    st.header("Login Aplikasi Badminton 🏸")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Masuk"):
        # Cek User Admin
        if username == "Fikri" and password == "haha":
            st.session_state['sudah_login'] = True
            st.session_state['user_role'] = "Admin"
            st.rerun() # Refresh halaman otomatis
            
        # Cek User Member
        elif username == "Member" and password == "abcd":
            st.session_state['sudah_login'] = True
            st.session_state['user_role'] = "Member"
            st.rerun()
            
        else:
            st.error("Username atau Password salah!")

# 3. Pengecekan Utama
if not st.session_state['sudah_login']:
    login_form()
    st.stop()  # ⛔ BERHENTI DI SINI kalau belum login!

# Pastikan nama file ini SAMA PERSIS dengan file Excel yang kamu bikin tadi
FILE_EXCEL = 'data_badminton.xlsx'

# --- FUNGSI 1: BACA GUDANG DATA ---
def load_data():
    """Membuka file Excel dan mengubahnya jadi DataFrame (Tabel Python)"""
    if os.path.exists(FILE_EXCEL):
        try:
            return pd.read_excel(FILE_EXCEL)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            return None
    else:
        # Jaga-jaga kalau filenya hilang, kita bikin tabel kosongan
        return pd.DataFrame(columns=['Tanggal', 'Jenis', 'Kategori', 'Nominal', 'Keterangan'])

# --- FUNGSI 2: TULIS KE GUDANG DATA ---
def simpan_data(df):
    """Menyimpan tabel Python kembali ke file Excel"""
    try:
        df.to_excel(FILE_EXCEL, index=False)
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")
        # --- 3. MEMBUAT TAMPILAN (INTERFACE) ---
st.title("🏸 Aplikasi Kas Badminton")
st.write("Catat pemasukan dan pengeluaran dengan mudah.")

# Muat data yang ada di Excel sekarang
df = load_data()

# Menu Navigasi di Sidebar (Kiri)

# --- LOGIKA MENU DINAMIS ---
if st.session_state['user_role'] == "Admin":
    # Kalau Admin, menunya lengkap
    opsi_menu = ["Input Data", "Laporan Kas", "Hapus Data"]
else:
    # Kalau Member, menu "Hapus Data" dihilangkan
    opsi_menu = ["Input Data", "Laporan Kas"]

# Masukkan opsi_menu ke dalam selectbox
menu = st.sidebar.selectbox("Pilih Menu", opsi_menu)

# === MENU 1: INPUT DATA ===
if menu == "Input Data":
    st.header("Tambah Transaksi Baru")

    df = load_data()

    def salin_nama():
        # Ambil isi Nama Member, masukkan ke Keterangan
        st.session_state['input_ket'] = st.session_state['input_member']

    # Bikin Formulir
    
    col1, col2 = st.columns(2) # Bagi layar jadi 2 kolom
    
    with col1:
        tanggal = st.date_input("Tanggal", datetime.now())
        member = st.text_input("Nama Member (Khusus Pemasukan)",key="input_member", on_change=salin_nama)
    
    with col2:
        # 1. Pilih Jenis (Pemasukan/Pengeluaran)
        if st.session_state['user_role'] == "Admin":
            opsi_jenis = ["Pemasukan", "Pengeluaran"]
        else:
            opsi_jenis = ["Pemasukan"]
            
        jenis = st.selectbox("Jenis", opsi_jenis)
        
        # 2. Tentukan Kategori (JANGAN SAMPAI HILANG)
        if jenis == "Pemasukan":
            opsi_kategori = ["Iuran"]
        else:
            opsi_kategori = ["Lapangan", "Kock"]
        
        kategori = st.selectbox("Kategori", opsi_kategori)

        # 3. Input Nominal (Logika Pintar V1.0)
        if st.session_state['user_role'] == "Member":
            angka_bawaan = 20000
        else:
            angka_bawaan = 0

        # Cek ingatan, kalau kosong kita isi paksa
        if "input_nominal" not in st.session_state:
            st.session_state["input_nominal"] = angka_bawaan

        nominal = st.number_input("Nominal (Rp)", min_value=0, step=5000, key="input_nominal")
        
        # ... (lanjut ke keterangan) ...
        ket = st.text_area("Keterangan Tambahan", key="input_ket")

        # Tombol Submit
        tombol_simpan = st.button("Simpan Data")

        if tombol_simpan:
            # 1. Siapkan data baru
            data_baru = pd.DataFrame([{
                'Tanggal': tanggal,
                'Jenis': jenis,
                'Kategori': kategori,
                'Nominal': nominal,
                'Keterangan': ket
            }])

            # 2. Gabungkan (Concatenate)
            df_update = pd.concat([df, data_baru], ignore_index=True)

            # 3. Simpan ke Excel
            simpan_data(df_update)
            
            st.success("✅ Data berhasil disimpan!")

            # Angkat bendera untuk putaran berikutnya
            st.session_state['bersihkan_form'] = True
        
             # Refresh halaman supaya logika di atas jalan
            st.rerun()

            # === MENU 2: LAPORAN KAS ===
elif menu == "Laporan Kas":
    st.header("Laporan Keuangan")
    
    # 1. BACA ULANG DATA (Penting biar data baru muncul!)
    df = load_data()
    df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
    
    # 2. Tampilkan Tabel
    st.dataframe(df)
    
    # 3. Hitung Ringkasan (Opsional)
    if not df.empty:
        st.write("---")
        total_masuk = df[df['Jenis'] == 'Pemasukan']['Nominal'].sum()
        total_keluar = df[df['Jenis'] == 'Pengeluaran']['Nominal'].sum()
        sisa = total_masuk - total_keluar
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Pemasukan", f"Rp {total_masuk:,.0f}")
        col2.metric("Pengeluaran", f"Rp {total_keluar:,.0f}")
        col3.metric("Sisa Kas", f"Rp {sisa:,.0f}")
        # === MENU 3: HAPUS DATA ===
elif menu == "Hapus Data":
    st.header("Hapus Data Transaksi")
    
    # 1. Baca Data
    df = load_data()
    df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
    
    # 2. Tampilkan Tabel (Supaya kamu bisa lihat nomor Index-nya)
    st.write("Lihat nomor (angka paling kiri) baris yang ingin dihapus:")
    st.dataframe(df)
    
    # 3. Logika Hapus
    if not df.empty:
        # Pilihan nomor index
        nomor_hapus = st.selectbox("Pilih Nomor Baris (Index) yang mau dihapus:", df.index)
        
        # Tombol Eksekusi
        if st.button("🗑️ Hapus Permanen"):
            try:
                # Proses Hapus baris
                df = df.drop(nomor_hapus)
                
                # Simpan perubahan ke Excel
                simpan_data(df)
                
                st.success(f"✅ Data baris ke-{nomor_hapus} berhasil dihapus!")
                
                # Paksa refresh halaman biar tabelnya update
                st.rerun()
                
            except Exception as e:
                st.error(f"Gagal menghapus: {e}")
    else:
        st.info("Belum ada data yang bisa dihapus.")