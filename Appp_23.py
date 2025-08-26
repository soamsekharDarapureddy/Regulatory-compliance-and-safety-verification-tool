# app.py
import streamlit as st
import pandas as pd
import pdfplumber
import openpyxl
import re
import os
import base64

# To parse .docx files, you need to install python-docx
try:
    import docx
except ImportError:
    st.error("The 'python-docx' library is not installed. Please install it by running: pip install python-docx")
    st.stop()

# ===============================================
# === GLOBAL CONFIG & STYLING ===
# ===============================================
st.set_page_config(page_title="Regulatory Compliance & Safety Tool", layout="wide")

st.markdown("""
<style>
:root { --accent:#0056b3; --panel:#f3f8fc; --shadow:#cfe7ff; }
.card{background:#fff; border-radius:10px; padding:12px 14px; margin-bottom:10px; border-left:8px solid #c9d6e8;}
.datasheet-card{ background: #ffffff; border: 1px solid #dee2e6; box-shadow: 0 4px 6px rgba(0,0,0,0.05); padding: 20px; border-radius: 15px; margin-top: 20px; }
.datasheet-title{ color: #0056b3; font-size: 1.8em; font-weight: 700; margin-bottom: 5px; }
.datasheet-subtitle{ color: #4a5568; font-size: 1.1em; font-weight: 500; margin-bottom: 15px; }
.spec-grid{ display: grid; grid-template-columns: 1fr 2fr; gap: 10px 20px; align-items: center; }
.spec-label{ font-weight: 600; color: #495057; text-align: right; }
.spec-value{ color: #212529; }
a {text-decoration: none; color: #0056b3; font-weight: 500;}
a:hover {text-decoration: underline;}
.main .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ===============================================
# === HEADER AND LOGO ===
# ===============================================
def get_image_as_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_base64 = get_image_as_base64("people_tech_logo.png")
if logo_base64:
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 25px;">
            <img src="data:image/png;base64,{logo_base64}" alt="Logo" style="height: 120px; margin-right: 25px;"/>
            <div>
                <h1 style="color:#0056b3; margin: 0; font-size: 2.2em; line-height: 1.0;">Regulatory Compliance</h1>
                <h2 style="color:#0056b3; margin: 0; font-size: 1.4em; line-height: 1.0;">& Safety Verification Tool</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("Logo file 'people_tech_logo.png' not found.")
    st.title("Regulatory Compliance & Safety Verification Tool")

# ===============================================
# === KNOWLEDGE BASES & DATABASE LOADING ===
# ===============================================
@st.cache_data
def load_bom_data():
    # This is the complete database from your Excel BOM, now hardcoded for reliability.
    bom_db = {
        'fh28-10s-0.5sh(05)': {'part_name': 'FH28-10S-0.5SH(05)', 'manufacturer': 'Hirose Electric Co Ltd', 'use': 'Board-to-FPC Connector'},
        'gcm155l81e104ke02d': {'part_name': '0.1uF Capacitor (GCM155L81E104KE02D)', 'manufacturer': 'Murata Electronics', 'use': 'Decoupling and Filtering'},
        'cga3e3x7s1a225k080ae': {'part_name': '2.2uF Capacitor (CGA3E3X7S1A225K080AE)', 'manufacturer': 'TDK Corporation', 'use': 'Bulk Decoupling'},
        'grt1555c1e220ja02j': {'part_name': '22pF Capacitor (GRT1555C1E220JA02J)', 'manufacturer': 'Murata Electronics', 'use': 'Tuning/Timing Circuits'},
        'grt155r61a475me13d': {'part_name': '4.7uF Capacitor (GRT155R61A475ME13D)', 'manufacturer': 'Murata Electronics', 'use': 'Decoupling'},
        'grt31cr61a476ke13l': {'part_name': '47uF Capacitor (GRT31CR61A476KE13L)', 'manufacturer': 'Murata Electronics', 'use': 'Bulk Capacitance'},
        'cga3e1x7r1e105k080ac': {'part_name': '1uF Capacitor (CGA3E1X7R1E105K080AC)', 'manufacturer': 'TDK Corporation', 'use': 'Decoupling'},
        'cga2b2c0g1h180j050ba': {'part_name': '18pF Capacitor (CGA2B2C0G1H180J050BA)', 'manufacturer': 'TDK Corporation', 'use': 'Tuning/Timing Circuits'},
        'c0402c103k4racauto': {'part_name': '10nF Capacitor (C0402C103K4RACAUTO)', 'manufacturer': 'KEMET', 'use': 'Filtering'},
        'gcm1555c1h101ja16d': {'part_name': '100pF Capacitor (GCM1555C1H101JA16D)', 'manufacturer': 'Murata Electronics', 'use': 'Filtering'},
        'grt155r71h104ke01d': {'part_name': '0.1uF/50V Capacitor (GRT155R71H104KE01D)', 'manufacturer': 'Murata Electronics', 'use': 'Decoupling'},
        'grt21br61e226me13l': {'part_name': '22uF Capacitor (GRT21BR61E226ME13L)', 'manufacturer': 'Murata Electronics', 'use': 'Bulk Decoupling'},
        'grt1555c1h150fa02d': {'part_name': '15pF Capacitor (GRT1555C1H150FA02D)', 'manufacturer': 'Murata Electronics', 'use': 'Tuning/Timing Circuits'},
        '0402yc222j4t2a': {'part_name': '2.2nF Capacitor (0402YC222J4T2A)', 'manufacturer': 'KYOCERA AVX', 'use': 'Filtering'},
        'gcm1555c1h560fa16d': {'part_name': '56pF Capacitor (GCM1555C1H560FA16D)', 'manufacturer': 'Murata Electronics', 'use': 'Tuning/Timing Circuits'},
        'grt1555c1h330fa02d': {'part_name': '33pF Capacitor (GRT1555C1H330FA02D)', 'manufacturer': 'Murata Electronics', 'use': 'Tuning/Timing Circuits'},
        'grt188c81a106me13d': {'part_name': '10uF Capacitor (GRT188C81A106ME13D)', 'manufacturer': 'Murata Electronics North America', 'use': 'Bulk Decoupling'},
        'umk212b7105kght': {'part_name': '1uF Capacitor (UMK212B7105KGHT)', 'manufacturer': 'Taiyo Yuden', 'use': 'Decoupling'},
        'c1206c104k5racauto': {'part_name': '0.1uF/50V Capacitor (C1206C104K5RACAUTO)', 'manufacturer': 'KEMET', 'use': 'Decoupling'},
        'grt31cr61h106ke01k': {'part_name': '10uF/50V Capacitor (GRT31CR61H106KE01K)', 'manufacturer': 'Murata Electronics', 'use': 'Bulk Decoupling'},
        'mcasu105sb7103kfna01': {'part_name': '0.01uF Capacitor (MCASU105SB7103KFNA01)', 'manufacturer': 'Taiyo Yuden', 'use': 'Filtering'},
        'c0402c333k4racauto': {'part_name': '33nF Capacitor (C0402C333K4RACAUTO)', 'manufacturer': 'KEMET', 'use': 'Filtering'},
        'cl10b474ko8vpnc': {'part_name': '0.47uF Capacitor (CL10B474KO8VPNC)', 'manufacturer': 'Samsung Electro-Mechanics', 'use': 'Decoupling'},
        'gcm155r71c224ke02d': {'part_name': '0.22uF Capacitor (GCM155R71C224KE02D)', 'manufacturer': 'Murata Electronics', 'use': 'Decoupling'},
        'gcm155r71h102ka37j': {'part_name': '1nF Capacitor (GCM155R71H102KA37J)', 'manufacturer': 'Murata Electronics', 'use': 'Filtering'},
        '50tpv330m10x10.5': {'part_name': '330uF/50V Capacitor (50TPV330M10X10.5)', 'manufacturer': 'Rubycon', 'use': 'Bulk Capacitance'},
        'cl31b684kbhwpne': {'part_name': '0.68uF Capacitor (CL31B684KBHWPNE)', 'manufacturer': 'Samsung Electro-Mechanics', 'use': 'Decoupling'},
        'gcm155r71h272ka37d': {'part_name': '2.7nF Capacitor (GCM155R71H272KA37D)', 'manufacturer': 'Murata Electronics', 'use': 'Filtering'},
        'edk476m050s9haa': {'part_name': '47uF/50V Capacitor (EDK476M050S9HAA)', 'manufacturer': 'KEMET', 'use': 'Bulk Capacitance'},
        'gcm155r71h332ka37j': {'part_name': '3.3nF Capacitor (GCM155R71H332KA37J)', 'manufacturer': 'Murata Electronics', 'use': 'Filtering'},
        'a768ke336m1hlae042': {'part_name': '33uF/50V Capacitor (A768KE336M1HLAE042)', 'manufacturer': 'KEMET', 'use': 'Bulk Capacitance'},
        'ac0402jrx7r9bb152': {'part_name': '1500pF Capacitor (AC0402JRX7R9BB152)', 'manufacturer': 'YAGEO', 'use': 'Filtering'},
        'd5v0h1b2lpq-7b': {'part_name': 'ESD Protection Diode (D5V0H1B2LPQ-7B)', 'manufacturer': 'Diodes Incorporated', 'use': 'ESD Protection'},
        'szmmbz9v1alt3g': {'part_name': 'Zener Diode 9.1V (SZMMBZ9V1ALT3G)', 'manufacturer': 'onsemi', 'use': 'Voltage Regulation'},
        'd24v0s1u2tq-7': {'part_name': 'TVS Diode (D24V0S1U2TQ-7)', 'manufacturer': 'Diodes Incorporated', 'use': 'Transient Voltage Suppression'},
        'b340bq-13-f': {'part_name': 'Schottky Diode (B340BQ-13-F)', 'manufacturer': 'Diodes Incorporated', 'use': 'Rectification'},
        'tld8s22ah': {'part_name': 'TVS Diode (TLD8S22AH)', 'manufacturer': 'Taiwan Semiconductor', 'use': 'Transient Voltage Suppression'},
        'b260aq-13-f': {'part_name': 'Schottky Diode (B260AQ-13-F)', 'manufacturer': 'Diodes Incorporated', 'use': 'Rectification'},
        'rb530sm-40fht2r': {'part_name': 'Schottky Diode (RB530SM-40FHT2R)', 'manufacturer': 'Rohm Semiconductor', 'use': 'Rectification'},
        '74279262': {'part_name': 'Ferrite Bead 120R/300mA (74279262)', 'manufacturer': 'Würth Elektronik', 'use': 'EMI Suppression'},
        '742792641': {'part_name': 'Ferrite Bead 300 Ohm/2A (742792641)', 'manufacturer': 'Würth Elektronik', 'use': 'EMI Suppression'},
        '742792625': {'part_name': 'Ferrite Bead 120 Ohm (742792625)', 'manufacturer': 'Würth Elektronik', 'use': 'EMI Suppression'},
        '742792150': {'part_name': 'Ferrite Bead 80 Ohm (742792150)', 'manufacturer': 'Würth Elektronik', 'use': 'EMI Suppression'},
        '78279220800': {'part_name': 'Ferrite Bead 80 Ohm (78279220800)', 'manufacturer': 'Würth Elektronik', 'use': 'EMI Suppression'},
        'voma617a-4x001t': {'part_name': 'Optocoupler (VOMA617A-4X001T)', 'manufacturer': 'Vishay', 'use': 'Signal Isolation'},
        '534260610': {'part_name': 'Header 6-pin (534260610)', 'manufacturer': 'Molex', 'use': 'Connector'},
        'fh52-40s-0.5sh(99)': {'part_name': 'Header 42-pin (FH52-40S-0.5SH(99))', 'manufacturer': 'Hirose Electric Co Ltd', 'use': 'Connector'},
        '5019530507': {'part_name': 'Connector (5019530507)', 'manufacturer': 'Molex', 'use': 'Connector'},
        'x8821wv-06l-n0sn': {'part_name': 'Connector (X8821WV-06L-N0SN)', 'manufacturer': 'XKB', 'use': 'Connector'},
        '744235510': {'part_name': 'Inductor (744235510)', 'manufacturer': 'Würth Elektronik', 'use': 'Power Inductor'},
        'lqw15an56nj8zd': {'part_name': '56nH Inductor (LQW15AN56NJ8ZD)', 'manufacturer': 'Murata Electronics', 'use': 'RF Inductor'},
        'spm7054vt-220m-d': {'part_name': '22uH Inductor (SPM7054VT-220M-D)', 'manufacturer': 'TDK Corporation', 'use': 'Power Inductor'},
        '744273801': {'part_name': 'Common Mode Choke (744273801)', 'manufacturer': 'Wurth Electronics Inc', 'use': 'EMI Filtering'},
        '74404084068': {'part_name': '6.8uH Inductor (74404084068)', 'manufacturer': 'Würth Elektronik', 'use': 'Power Inductor'},
        '744231091': {'part_name': 'Common Mode Choke (744231091)', 'manufacturer': 'Würth Elektronik', 'use': 'EMI Filtering'},
        'mlz2012m6r8htd25': {'part_name': '6.8uH Inductor (MLZ2012M6R8HTD25)', 'manufacturer': 'TDK Corporation', 'use': 'Power Inductor'},
        'rq3g270bjfratcb': {'part_name': 'P-Channel MOSFET (RQ3G270BJFRATCB)', 'manufacturer': 'Rohm Semiconductor', 'use': 'Switching'},
        'pja138k-au_r1_000a1': {'part_name': 'MOSFET (PJA138K-AU_R1_000A1)', 'manufacturer': 'Panjit International Inc.', 'use': 'Switching'},
        'dmp2070uq-7': {'part_name': 'MOSFET (DMP2070UQ-7)', 'manufacturer': 'Diodes Incorporated', 'use': 'Switching'},
        'ac0402jr-070rl': {'part_name': '0R Resistor (AC0402JR-070RL)', 'manufacturer': 'YAGEO', 'use': 'Jumper'},
        'ac0402fr-07100kl': {'part_name': '100K Resistor (AC0402FR-07100KL)', 'manufacturer': 'YAGEO', 'use': 'Pull-up/Pull-down'},
        'rmcf0402ft158k': {'part_name': '158K Resistor (RMCF0402FT158K)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft30k0': {'part_name': '30K Resistor (RMCF0402FT30K0)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft127k': {'part_name': '127K Resistor (RMCF0402FT127K)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmc10k204fth': {'part_name': '200K Resistor (RMC10K204FTH)', 'manufacturer': 'KAMAYA', 'use': 'Biasing'},
        'erj-2rkf2201x': {'part_name': '2.2K Resistor (ERJ-2RKF2201X)', 'manufacturer': 'Panasonic', 'use': 'Biasing'},
        'erj-2rkf1002x': {'part_name': '10K Resistor (ERJ-2RKF1002X)', 'manufacturer': 'Panasonic', 'use': 'Pull-up/Pull-down'},
        'wr04x1004ftl': {'part_name': '1M Resistor (WR04X1004FTL)', 'manufacturer': 'Walsin Technology', 'use': 'Biasing'},
        'wr04x10r0ftl': {'part_name': '10R Resistor (WR04X10R0FTL)', 'manufacturer': 'Walsin Technology', 'use': 'Current Limiting'},
        'rc0603fr-0759rl': {'part_name': '59R Resistor (RC0603FR-0759RL)', 'manufacturer': 'YAGEO', 'use': 'Current Limiting'},
        'rmc1/16jptp': {'part_name': '0R Resistor (RMC1/16JPTP)', 'manufacturer': 'Kamaya Inc.', 'use': 'Jumper'},
        'ac0402fr-07100rl': {'part_name': '100R Resistor (AC0402FR-07100RL)', 'manufacturer': 'YAGEO', 'use': 'Current Limiting'},
        'ac0402fr-076k04l': {'part_name': '6.04K Resistor (AC0402FR-076K04L)', 'manufacturer': 'YAGEO', 'use': 'Biasing'},
        'ac0402fr-07510rl': {'part_name': '510R Resistor (AC0402FR-07510RL)', 'manufacturer': 'YAGEO', 'use': 'Current Limiting'},
        'crgcq0402f56k': {'part_name': '56K Resistor (CRGCQ0402F56K)', 'manufacturer': 'TE Connectivity', 'use': 'Biasing'},
        'rmcf0402ft24k9': {'part_name': '24.9K Resistor (RMCF0402FT24K9)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft5k36': {'part_name': '5.36K Resistor (RMCF0402FT5K36)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0603ft12k0': {'part_name': '12K Resistor (RMCF0603FT12K0)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft210k': {'part_name': '210K Resistor (RMCF0402FT210K)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'ltr18ezpfsr015': {'part_name': '0.015R Resistor (LTR18EZPFSR015)', 'manufacturer': 'Rohm Semiconductor', 'use': 'Current Sensing'},
        'erj-pa2j102x': {'part_name': '1K Resistor (ERJ-PA2J102X)', 'manufacturer': 'Panasonic', 'use': 'Biasing'},
        'rmcf0402ft5k10': {'part_name': '5.1K Resistor (RMCF0402FT5K10)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0603ft100r': {'part_name': '100R Resistor (RMCF0603FT100R)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Current Limiting'},
        'ac0402jr-074k7l': {'part_name': '4.7K Resistor (AC0402JR-074K7L)', 'manufacturer': 'YAGEO', 'use': 'Biasing'},
        'crf0805-fz-r010elf': {'part_name': '0.01R Resistor (CRF0805-FZ-R010ELF)', 'manufacturer': 'Bourns Inc.', 'use': 'Current Sensing'},
        'rmcf0402ft3k16': {'part_name': '3.16K Resistor (RMCF0402FT3K16)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft3k48': {'part_name': '3.48K Resistor (RMCF0402FT3K48)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft1k50': {'part_name': '1.5K Resistor (RMCF0402FT1K50)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf0402ft4k02': {'part_name': '4.02K Resistor (RMCF0402FT4K02)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'rmcf1206zt0r00': {'part_name': '0R Resistor (RMCF1206ZT0R00)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Jumper'},
        'rmcf0402ft402k': {'part_name': '402K Resistor (RMCF0402FT402K)', 'manufacturer': 'Stackpole Electronics Inc', 'use': 'Biasing'},
        'ac0603fr-7w20kl': {'part_name': '20K Resistor (AC0603FR-7W20KL)', 'manufacturer': 'YAGEO', 'use': 'Biasing'},
        'h164yp': {'part_name': 'Ethernet PHY (H164YP)', 'manufacturer': 'AGENEW', 'use': 'Ethernet Interface'},
        'ap63357qzv-7': {'part_name': 'Buck Converter (AP63357QZV-7)', 'manufacturer': 'Diodes Incorporated', 'use': 'Power Supply Conversion'},
        'pca9306idcurq1': {'part_name': 'Voltage-Level Translator (PCA9306IDCURQ1)', 'manufacturer': 'Texas Instruments', 'use': 'I2C Level Shifting'},
        'mcp2518fdt-e/sl': {'part_name': 'CAN FD Controller (MCP2518FDT-E/SL)', 'manufacturer': 'Microchip Technology', 'use': 'CAN Bus Interface'},
        'lt8912b': {'part_name': 'MIPI Bridge (LT8912B)', 'manufacturer': 'Lontium', 'use': 'Display/Camera Interface'},
        'sn74lv1t34qdckrq1': {'part_name': 'Voltage Level Translator (SN74LV1T34QDCKRQ1)', 'manufacturer': 'Texas Instruments', 'use': 'Logic Level Shifting'},
        'ncp164csnadjt1g': {'part_name': 'LDO Regulator (NCP164CSNADJT1G)', 'manufacturer': 'onsemi', 'use': 'Power Supply Regulation'},
        '20279-001e-03': {'part_name': 'Connector (20279-001E-03)', 'manufacturer': 'I-PEX', 'use': 'RF Connector'},
        'ncv8161asn180t1g': {'part_name': 'LDO Regulator (NCV8161ASN180T1G)', 'manufacturer': 'onsemi', 'use': 'Power Supply Regulation'},
        'drtr5v0u2sr-7': {'part_name': 'ESD Protection Diode (DRTR5V0U2SR-7)', 'manufacturer': 'Diodes Incorporated', 'use': 'ESD Protection'},
        'ncv8161asn330t1g': {'part_name': 'LDO Regulator (NCV8161ASN330T1G)', 'manufacturer': 'onsemi', 'use': 'Power Supply Regulation'},
        'nxs0102dc-q100h': {'part_name': 'Level Translator (NXS0102DC-Q100H)', 'manufacturer': 'Nexperia', 'use': 'Logic Level Shifting'},
        'cf0505xt-1wr3': {'part_name': 'DC/DC Converter (CF0505XT-1WR3)', 'manufacturer': 'MORNSUN', 'use': 'Isolated Power Supply'},
        'iam-20680ht': {'part_name': 'IMU Sensor (IAM-20680HT)', 'manufacturer': 'TDK InvenSense', 'use': 'Motion Sensing'},
        'attiny1616-szt-vao': {'part_name': 'MCU (ATTINY1616-SZT-VAO)', 'manufacturer': 'Microchip', 'use': 'Microcontroller'},
        'qmc5883l': {'part_name': 'Magnetometer (QMC5883L)', 'manufacturer': 'QST', 'use': 'Magnetic Field Sensing'},
        'lm76202qpwprq1': {'part_name': 'Ideal Diode Controller (LM76202QPWPRQ1)', 'manufacturer': 'Texas Instruments', 'use': 'Reverse Polarity Protection'},
        'bd83a04efv-me2': {'part_name': 'LED Driver (BD83A04EFV-ME2)', 'manufacturer': 'Rohm Semiconductor', 'use': 'LED Driving'},
        'ecs-200-12-33q-jes-tr': {'part_name': '20MHz Crystal (ECS-200-12-33Q-JES-TR)', 'manufacturer': 'ECS Inc.', 'use': 'Clock Generation'},
        'ecs-250-12-33q-jes-tr': {'part_name': '25MHz Crystal (ECS-250-12-33Q-JES-TR)', 'manufacturer': 'ECS Inc.', 'use': 'Clock Generation'},
        'aggbp.25a.07.0060a': {'part_name': 'GPS Antenna (AGGBP.25A.07.0060A)', 'manufacturer': 'Toaglas', 'use': 'GPS Signal Reception'},
        'y4ete00a0aa': {'part_name': 'LTE Antenna (Y4ETE00A0AA)', 'manufacturer': 'Quectel', 'use': 'LTE Signal Reception'},
        'yf0023aa': {'part_name': 'WIFI/BT Antenna (YF0023AA)', 'manufacturer': 'Quectel', 'use': 'Wi-Fi/Bluetooth Signal Reception'}
    }
    return bom_db

ENRICHED_DB = {
    "ecmf04-4hswm10y": {
        "part_name": "Common Mode Filter with ESD Protection", "use": "EMI/RFI filtering and ESD protection for high-speed differential lines.",
        "manufacturer": "STMicroelectronics", "category": "Filters", "sub_category": "Common Mode Chokes", "series": "ECMF",
        "packaging": "Tape & Reel (TR)", "part_status": "Active", "filter_type": "Signal Line", "number_of_lines": 4,
        "current_rating_max_ma": 100, "dcr_max_ohm": 5, "operating_temp_min_c": -40, "operating_temp_max_c": 85,
        "features": "TVS Diode ESD Protection", "mounting_type": "Surface Mount", "size_dimension_mm": "2.60mm x 1.35mm",
        "height_max_mm": 0.55, "package_case": "10-UFDFN", "base_product_number": "ECMF04"
    },
    "zldo1117qg33ta": {
        "part_name": "LDO Voltage Regulator, Fixed 3.3V 1A", "use": "Low-dropout positive fixed-mode regulator for low-voltage IC applications.",
        "manufacturer": "Diodes Incorporated", "category": "Integrated Circuits (ICs)", "sub_category": "PMIC - Voltage Regulators - Linear",
        "series": "ZLDO1117", "packaging": "SOT-223", "part_status": "Active", "output_type": "Fixed",
        "voltage_output_v": 3.3, "voltage_input_max_v": 18, "voltage_dropout_max_v": 1.2, "current_output_a": 1,
        "psrr": "80dB (120Hz)", "operating_temp_min_c": -40, "operating_temp_max_c": 125,
        "features": "Output Current Limiting, Thermal Shutdown", "mounting_type": "Surface Mount", "package_case": "SOT-223-3",
        "qualification": "AEC-Q100"
    },
    "iso1042bqdwvq1": {
        "part_name": "Isolated CAN Transceiver with 70-V Bus Fault Protection", "use": "Galvanically-isolated CAN transceiver for automotive and industrial applications.",
        "manufacturer": "Texas Instruments", "category": "Interface ICs", "sub_category": "CAN Interface IC",
        "series": "ISO1042", "type": "High Speed CAN Transceiver", "mounting_style": "SMD/SMT", "package_case": "SOIC-8",
        "data_rate": "5 Mb/s", "num_drivers": 1, "num_receivers": 1, "supply_voltage_min_v": 1.71,
        "supply_voltage_max_v": 5.5, "operating_temp_min_c": -40, "operating_temp_max_c": 125,
        "operating_supply_current_ma": 43, "esd_protection_kv": 16, "qualification": "AEC-Q100",
        "packaging": "Reel, Cut Tape, MouseReel", "power_dissipation_mw": 385, "propagation_delay_ns": 76,
        "unit_weight_mg": 392
    }
}

COMBINED_DB = {**load_bom_data(), **ENRICHED_DB}
KEYWORD_TO_STANDARD_MAP = { "gps": "NMEA 0183", "can": "ISO 11898", "ip rating": "IEC 60529" }
TEST_CASE_KNOWLEDGE_BASE = { "over-voltage": {"requirement": "Withstand over-voltage", "equipment": ["PSU", "DMM"]} }

# ===============================================
# === HELPER FUNCTIONS (FOR ALL MODULES) ===
# ===============================================
def intelligent_parser(text: str):
    extracted_tests = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        test_data = {"TestName": "N/A", "Result": "N/A", "Standard": "N/A", "Description": "N/A"}
        patterns = [
            r'^(.*?)\s*-->\s*(Passed|Failed|Success)\s*-->\s*(.+)$',
            r'^(.*?)\s*:\s*(PASS|FAIL|PASSED|FAILED)$'
        ]
        match1 = re.match(patterns[0], line, re.I)
        match2 = re.match(patterns[1], line, re.I)
        if match1:
            test_data.update({"TestName": match1.group(1).strip(), "Result": "PASS" if match1.group(2).lower() in ["passed", "success"] else "FAIL", "Description": match1.group(3).strip()})
        elif match2:
            test_data.update({"TestName": match2.group(1).strip(), "Result": "PASS" if match2.group(2).lower() in ["pass", "passed"] else "FAIL"})
        else:
            continue
        for keyword, standard in KEYWORD_TO_STANDARD_MAP.items():
            if keyword in test_data["TestName"].lower():
                test_data["Standard"] = standard
        extracted_tests.append(test_data)
    return extracted_tests

def parse_report(uploaded_file):
    if not uploaded_file: return []
    try:
        file_extension = os.path.splitext(uploaded_file.name.lower())[1]
        if file_extension in ['.csv', '.xlsx']:
            df = pd.read_csv(uploaded_file) if file_extension == '.csv' else pd.read_excel(uploaded_file)
            df.columns = [str(c).strip().lower() for c in df.columns]
            rename_map = {'test': 'TestName', 'standard': 'Standard', 'result': 'Result', 'description': 'Description'}
            df.rename(columns=rename_map, inplace=True)
            return df.to_dict('records')
        elif file_extension == '.pdf':
             with pdfplumber.open(uploaded_file) as pdf:
                content = "".join(page.extract_text() + "\n" for page in pdf.pages if page.extract_text())
        else:
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
        return intelligent_parser(content)
    except Exception as e:
        st.error(f"An error occurred while parsing the report: {e}")
        return []

def display_test_card(test_case, color):
    details = f"<b>🧪 Test:</b> {test_case.get('TestName', 'N/A')}<br>"
    for key, label in {'Standard': '📘 Standard', 'Description': '💬 Description'}.items():
        if pd.notna(value := test_case.get(key)) and str(value).strip() and value != 'N/A':
            details += f"<b>{label}:</b> {value}<br>"
    st.markdown(f"<div class='card' style='border-left-color:{color};'>{details}</div>", unsafe_allow_html=True)

def display_datasheet_details(part_number, data):
    st.markdown(f"<div class='datasheet-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='datasheet-title'>{data.get('part_name', part_number.upper())}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='datasheet-subtitle'><b>Manufacturer:</b> {data.get('manufacturer', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown(f"<p><b>Primary Use / Application:</b> {data.get('use', 'General Purpose')}</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid #e9ecef; margin: 15px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<div class='spec-grid'>", unsafe_allow_html=True)
    spec_order = [
        ("Category", "category"), ("Series", "series"), ("Type", "type"), ("Mounting Style", "mounting_style"),
        ("Package / Case", "package_case"), ("Data Rate", "data_rate"),
        ("Number of Drivers/Receivers", "drivers_receivers"), ("Supply Voltage", "supply_voltage"),
        ("Operating Temperature", "operating_temp_range"), ("Operating Supply Current", "operating_supply_current_ma", "mA"),
        ("ESD Protection", "esd_protection_kv", "kV"), ("Qualification", "qualification"),
        ("Packaging", "packaging"), ("Power Dissipation", "power_dissipation_mw", "mW"),
        ("Propagation Delay", "propagation_delay_ns", "ns"), ("Unit Weight", "unit_weight_mg", "mg"),
    ]

    # Pre-format combined fields
    if "num_drivers" in data and "num_receivers" in data:
        data["drivers_receivers"] = f"{data['num_drivers']} Driver / {data['num_receivers']} Receiver"
    if "supply_voltage_min_v" in data and "supply_voltage_max_v" in data:
        data["supply_voltage"] = f"{data['supply_voltage_min_v']}V to {data['supply_voltage_max_v']}V"
    if "operating_temp_min_c" in data and "operating_temp_max_c" in data:
        data["operating_temp_range"] = f"{data['operating_temp_min_c']}°C to {data['operating_temp_max_c']}°C"
    
    has_specs = False
    for label, key, *unit in spec_order:
        if key in data and data.get(key) is not None:
            has_specs = True
            value = f"{data[key]} {unit[0]}" if unit and data[key] else data[key]
            st.markdown(f"<div class='spec-label'>{label}</div><div class='spec-value'>{value}</div>", unsafe_allow_html=True)
            
    if not has_specs:
        st.markdown("<div class='spec-label'>Details</div><div class='spec-value'>Standard component data loaded from BOM. For full datasheet specifications, please refer to the manufacturer's website.</div>", unsafe_allow_html=True)
        
    st.markdown("</div></div>", unsafe_allow_html=True)

# ===============================================
# === MAIN APP LAYOUT & NAVIGATION ===
# ===============================================
st.sidebar.title("Navigation")
option = st.sidebar.radio("Go to", ("Test Report Verification", "Component Information", "Test Requirement Generation"))

# ===============================================
# === 1. TEST REPORT VERIFICATION MODULE ===
# ===============================================
if option == "Test Report Verification":
    st.header("Test Report Verification")
    st.caption("Upload and analyze test reports from various formats.")
    uploaded_file = st.file_uploader("Upload a report file", type=["pdf", "xlsx", "csv", "txt"])
    if uploaded_file:
        parsed_data = parse_report(uploaded_file)
        if parsed_data:
            st.success(f"Successfully parsed {len(parsed_data)} test results.")
            passed = [t for t in parsed_data if "PASS" in str(t.get("Result", "")).upper()]
            failed = [t for t in parsed_data if "FAIL" in str(t.get("Result", "")).upper()]
            others = [t for t in parsed_data if not ("PASS" in str(t.get("Result", "")).upper() or "FAIL" in str(t.get("Result", "")).upper())]
            
            st.markdown(f"### Analysis Complete: {len(passed)} Passed, {len(failed)} Failed, {len(others)} Other")
            if passed:
                with st.expander("✅ Passed Cases", expanded=True):
                    for t in passed: display_test_card(t, '#28a745')
            if failed:
                with st.expander("❌ Failed Cases", expanded=True):
                    for t in failed: display_test_card(t, '#dc3545')
            if others:
                with st.expander("ℹ️ Other/Informational Items"):
                    for t in others: display_test_card(t, '#6c757d')
        else:
            st.warning("No recognizable test data was extracted from the report.")

# ===============================================
# === 2. COMPONENT INFORMATION MODULE ===
# ===============================================
elif option == "Component Information":
    st.header("Component Key Information")
    st.caption("Search the complete BOM for detailed component specifications.")
    
    part_q = st.text_input("Enter Manufacturer Part Number for Detailed Lookup", placeholder="e.g., iso1042bqdwvq1").lower().strip()
    
    if st.button("Search Component"):
        if part_q:
            key = next((k for k in COMBINED_DB if part_q in k.lower()), None)
            if key:
                st.session_state.found_component = {"part_number": key, **COMBINED_DB[key]}
            else:
                st.session_state.found_component = {}
                st.warning("Component not found in the internal database.")
    
    if 'found_component' in st.session_state and st.session_state.found_component:
        display_datasheet_details(st.session_state.found_component['part_number'], st.session_state.found_component)

# ===============================================
# === 3. TEST REQUIREMENT GENERATION MODULE ===
# ===============================================
elif option == "Test Requirement Generation":
    st.header("Test Requirement Generation")
    st.caption("Automatically generate formal test requirements from keywords.")
    
    text = st.text_area("Enter test keywords (one per line)", "over-voltage test\nCAN bus functionality\nIP67 rating check", height=100)
    
    if st.button("Generate Requirements"):
        cases = [l.strip() for l in text.split("\n") if l.strip()]
        if cases:
            st.markdown("#### Generated Requirements")
            for i, case in enumerate(cases):
                req = next((info for key, info in TEST_CASE_KNOWLEDGE_BASE.items() if key in case.lower()), {"requirement": "Generic requirement - system must be tested as described.", "equipment": ["N/A"]})
                html = f"""
                <div class='card' style='border-left-color:#7c3aed;'>
                    <b>Test Case:</b> {case.title()}<br>
                    <b>Requirement ID:</b> REQ-{i+1:03d}<br>
                    <b>Requirement:</b> {req['requirement']}<br>
                    <b>Suggested Equipment:</b> {', '.join(req['equipment'])}
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
