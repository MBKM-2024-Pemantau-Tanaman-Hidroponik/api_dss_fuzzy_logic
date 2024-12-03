from flask import Flask, request, jsonify
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("G:\\KULIAH\\SCREEN_HOUSE_MBKM_2024\\monitoring-screenhouse-firebase-adminsdk-aljcq-fe24724aeb.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://monitoring-screenhouse-default-rtdb.firebaseio.com/'
    })
    
# Define Fuzzy Logic System
suhu = ctrl.Antecedent(np.arange(0, 51, 0.1), 'suhu')
kelembapan_udara = ctrl.Antecedent(np.arange(0, 101, 0.1), 'kelembapan_udara')
kelembapan_tanah = ctrl.Antecedent(np.arange(0, 101, 0.1), 'kelembapan_tanah')
ph_air = ctrl.Antecedent(np.arange(0, 15, 0.1), 'ph_air')
tds = ctrl.Antecedent(np.arange(0, 2501, 0.1), 'tds')
tindakan = ctrl.Consequent(np.arange(0, 7, 1), 'tindakan')

# Membership Functions
suhu['dingin'] = fuzz.trimf(suhu.universe, [0, 15, 20])
suhu['normal'] = fuzz.trimf(suhu.universe, [21, 27, 35])
suhu['panas'] = fuzz.trimf(suhu.universe, [30, 40, 50])

kelembapan_udara['rendah'] = fuzz.trimf(kelembapan_udara.universe, [0, 40, 50])
kelembapan_udara['sedang'] = fuzz.trimf(kelembapan_udara.universe, [50, 60, 85])
kelembapan_udara['tinggi'] = fuzz.trimf(kelembapan_udara.universe, [70, 90, 100])

kelembapan_tanah['kering'] = fuzz.trimf(kelembapan_tanah.universe, [0, 40, 50])
kelembapan_tanah['normal'] = fuzz.trimf(kelembapan_tanah.universe, [50, 60, 85])
kelembapan_tanah['basah'] = fuzz.trimf(kelembapan_tanah.universe, [70, 90, 100])

ph_air['asam'] = fuzz.trimf(ph_air.universe, [0, 5, 6.5])
ph_air['netral'] = fuzz.trimf(ph_air.universe, [6.5, 7, 8])
ph_air['basa'] = fuzz.trimf(ph_air.universe, [7.5, 10, 14])

tds['rendah'] = fuzz.trimf(tds.universe, [0, 400, 600])
tds['sedang'] = fuzz.trimf(tds.universe, [600, 1000, 1200])
tds['tinggi'] = fuzz.trimf(tds.universe, [1200, 2000, 2500])

tindakan['siram_air'] = fuzz.trimf(tindakan.universe, [0, 0, 1])
tindakan['sprayer_misting'] = fuzz.trimf(tindakan.universe, [1, 2, 3])
tindakan['tambahkan_nutrisi'] = fuzz.trimf(tindakan.universe, [2, 3, 4])
tindakan['blower_fan'] = fuzz.trimf(tindakan.universe, [3, 4, 5])
tindakan['pemantauan'] = fuzz.trimf(tindakan.universe, [4, 5, 6])

# Rules
rule1 = ctrl.Rule(suhu['panas'], tindakan['blower_fan'])
rule2 = ctrl.Rule(kelembapan_udara['rendah'], tindakan['sprayer_misting'])
rule3 = ctrl.Rule(kelembapan_tanah['kering'], tindakan['siram_air'])
rule4 = ctrl.Rule(suhu['panas'] & kelembapan_tanah['kering'], tindakan['siram_air'])
rule5 = ctrl.Rule(suhu['panas'] & kelembapan_udara['rendah'], tindakan['sprayer_misting'])
rule6 = ctrl.Rule(ph_air['asam'] & tds['rendah'], tindakan['tambahkan_nutrisi'])
rule7 = ctrl.Rule(tds['rendah'], tindakan['tambahkan_nutrisi'])
rule8 = ctrl.Rule(suhu['normal'] & kelembapan_tanah['basah'] & kelembapan_udara['sedang'] & ph_air['netral'] & tds['sedang'], tindakan['pemantauan'])

# Control System
dss_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
dss_simulation = ctrl.ControlSystemSimulation(dss_ctrl)

@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    try:
          # Retrieve sensor data
        data = request.json
        print("Received Input Data:", data)  # Debugging: Log inputs
        
        # Retrieve sensor data
        data = request.json
        suhu_value = data['suhu']
        kelembapan_udara_value = data['kelembapan_udara']
        kelembapan_tanah_value = data['kelembapan_tanah']
        ph_air_value = data['ph_air']
        tds_value = data['tds']

        # Apply Fuzzy Logic
        dss_simulation.input['suhu'] = suhu_value
        dss_simulation.input['kelembapan_udara'] = kelembapan_udara_value
        dss_simulation.input['kelembapan_tanah'] = kelembapan_tanah_value
        dss_simulation.input['ph_air'] = ph_air_value
        dss_simulation.input['tds'] = tds_value
        
        print("Fuzzy Input:", dss_simulation.input)  # Debugging: Log inputs to Fuzzy System
        dss_simulation.compute()
        print("Fuzzy Output After Compute:", dss_simulation.output)  # Debugging: Log outputs

        hasil_tindakan = dss_simulation.output['tindakan']
        
          # Determine Recommendation
        if hasil_tindakan < 1:
            rekomendasi = "Siram Air"
        elif 1 <= hasil_tindakan < 3:
            rekomendasi = "Aktifkan Sprayer Misting"
        elif 2 <= hasil_tindakan < 4:
            rekomendasi = "Tambahkan Nutrisi"
        elif 3 <= hasil_tindakan < 5:
            rekomendasi = "Aktifkan Kipas Blower"
        elif 4 <= hasil_tindakan <= 6:
            rekomendasi = "Aman Terkendali"
        else:
            rekomendasi = "Tidak ada rekomendasi"

        return jsonify({"recommendation": rekomendasi})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Replace '192.168.x.x' with your actual IP address
    app.run(host='192.168.18.22', port=80, debug=True)

