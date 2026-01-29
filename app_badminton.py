import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- KONEKSI DENGAN CACHE (ANTI ERROR 429) ---
# Fungsi ini dibungkus cache biar ngga bolak-balik login ke Google
@st.cache_resource
def connect_to_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Panggil Secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    # Buka Sheet (Pastikan nama sheet "TES" sesuai)
    return client.open("TES").sheet1

# --- MEMANGGIL KONEKSI ---
try:
    sheet = connect_to_google_sheet()
except Exception as e:
    st.error(f"❌ Gagal Konek: {e}")
    st.stop()

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


# --- FUNGSI 1: BACA GUDANG DATA ---
def load_data():
    # Tarik semua data dari Google Sheet
    data = sheet.get_all_records()
    
    # Ubah jadi tabel rapi (DataFrame)
    df = pd.DataFrame(data)
    
    # Sedikit trik: Kalau datanya kosong, kita buat kerangka kosong biar nggak error
    if df.empty:
        return pd.DataFrame(columns=["Tanggal", "Member", "Jenis", "Kategori", "Nominal", "Keterangan"])
        
    return df

st.title("🏸 Catatan Keuangan Badminton")
st.subheader("Bantu Admin Input data yaa 😊🙏")
st.write("Input Pembayaran Kamu Disini 👇👇.")

df = load_data()
# Menu Navigasi di Sidebar (Kiri)

# --- LOGIKA MENU DINAMIS ---
if st.session_state['user_role'] == "Admin":
    # Kalau Admin, menunya lengkap
    opsi_menu = ["Input Data", "Laporan Kas", "Hapus Data"]
else:
    # Kalau Member, menu "Hapus Data" dihilangkan
    opsi_menu = ["Laporan Kas"]

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
            # --- LOGIKA BARU: KIRIM KE GOOGLE SHEETS ---
            
            # 1. Ubah Tanggal jadi Teks (biar Google gak bingung)
            tanggal_str = str(tanggal)

            # 2. Susun data dalam satu baris (Urutan harus sama dengan kolom di Google Sheet!)
            baris_baru = [tanggal_str, member, jenis, kategori, nominal, ket]

            # 3. Kirim ke Awan ☁️
            sheet.append_row(baris_baru)
            
            st.success("✅ Berhasil simpan ke Google Drive!")
            
            # 4. Angkat bendera untuk bersih-bersih form
            st.session_state['bersihkan_form'] = True
            
            # 5. Refresh
            st.rerun()

            # === MENU 2: LAPORAN KAS ===
elif menu == "Laporan Kas":
    # --- LOGIKA FILTER TANGGAL (UPDATE BARU) ---
    # --- LOGIKA LAPORAN & HITUNG MEMBER (UPDATE) ---
    st.markdown("---")
    st.header("📊 Laporan Keuangan & Absensi")
    
    if not df.empty:
        # 1. Filter Tanggal
        daftar_tanggal = sorted(df['Tanggal'].unique().tolist(), reverse=True)
        opsi_pilihan = ["Semua Waktu"] + daftar_tanggal
        pilih_periode = st.selectbox("📅 Pilih Periode Laporan:", opsi_pilihan)
        
        # 2. Filter Data
        if pilih_periode == "Semua Waktu":
            df_tampil = df
            judul_ket = "Sisa Kas (Total)"
            judul_absen = "Total Kunjungan Member"
        else:
            df_tampil = df[df['Tanggal'] == pilih_periode]
            judul_ket = f"Sisa Kas ({pilih_periode})"
            judul_absen = f"Member Hadir ({pilih_periode})"
    
        # --- RUMUS 'COUNTIF' VERSI PYTHON ---
        df_member = df_tampil[df_tampil['Nominal'] == 20000]
        jumlah_member = len(df_member)
    
        # Hitung Duit
        total_masuk = df_tampil[df_tampil['Jenis'] == 'Pemasukan']['Nominal'].sum()
        total_keluar = df_tampil[df_tampil['Jenis'] == 'Pengeluaran']['Nominal'].sum()
        sisa_kas = total_masuk - total_keluar
        
        # --- LOGIKA WARNA TEKS (Pengeluaran = Merah) ---
        # (Perhatikan: def ini sekarang menjorok ke dalam, sejajar dengan filter di atas)
        def warna_teks_saja(row):
            if row['Jenis'] == 'Pengeluaran':
                return ['color: #D32F2F'] * len(row) 
            else:
                return [''] * len(row)

        # Terapkan warnanya
        df_berwarna = df_tampil.style.apply(warna_teks_saja, axis=1)

        # --- TAMPILKAN 4 KARTU SKOR ---
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Pemasukan", f"Rp {total_masuk:,}")
        col2.metric("Pengeluaran", f"Rp {total_keluar:,}")
        
        # Logika Minus Merah
        if sisa_kas < 0:
            col3.markdown(f"<p style='color:gray; margin-bottom:0;'>{judul_ket}</p>", unsafe_allow_html=True)
            col3.markdown(f"<h2 style='color:red; margin-top:0;'>Rp {sisa_kas:,}</h2>", unsafe_allow_html=True)
        else:
            col3.metric(judul_ket, f"Rp {sisa_kas:,}")
        
        col4.metric(judul_absen, f"{jumlah_member} Orang")

        # --- TAMPILKAN TABEL ---
        st.write(f"**Rincian Transaksi ({pilih_periode}):**")
        st.dataframe(df_berwarna, height=600, use_container_width=True)
        
        # Fitur Download
        csv = df_tampil.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download Laporan",
            data=csv,
            file_name=f'Laporan_{pilih_periode}.csv',
            mime='text/csv',
        )
    
    else:
        # Else ini sejajar dengan if not df.empty di atas
        st.info("Belum ada data laporan.")

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
                # --- PERBAIKAN DI SINI ---
                # Rumus: Index + 2 (Karena index mulai dari 0, dan Baris 1 di sheet adalah Judul)
                baris_di_sheet = int(nomor_hapus) + 2
                
                # Perintah langsung ke Google Sheet
                sheet.delete_rows(baris_di_sheet)
                # -------------------------

                st.success(f"✅ Data baris ke-{nomor_hapus} (Baris Sheet {baris_di_sheet}) berhasil dihapus permanen!")
                
                # Kita kasih jeda dikit biar pesan suksesnya sempat kebaca sebelum refresh
                import time
                time.sleep(1)
                
                # Refresh halaman biar tabelnya update dari sumber aslinya
                st.rerun()
                
            except Exception as e:
                st.error(f"Gagal menghapus: {e}")
    else:
        st.info("Belum ada data yang bisa dihapus.")






















