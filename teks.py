import re 
import sqlite3 
import pandas as pd 

from flask import Flask, jsonify, request 
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from 

app = Flask(__name__)

app.json_encoder = LazyJSONEncoder

# Merubah tulisan template halaman host 
swagger_template = dict(
    info = {
        'title': LazyString(lambda: 'API Text Output'),
        'version': LazyString(lambda: '1.0.0 // BETA'),
        'description': LazyString(lambda: 'Text Cleansing Output Clean text'),
    },
    host = LazyString(lambda: request.host)
)

# Konfigurasi alamat halaman akses, dll
swagger_config = {
    'headers': [],
    'specs': [
        {
            'endpoint': 'docs',
            'route': '/docs.json',
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route':'/'
}

# Menggabungkan template dan konfigurasi dalam satu variabel
swagger = Swagger(app, template = swagger_template, config = swagger_config)

# Fungsi menjadikan tulisan kecil semua 
def lowercase(huruf):
    return huruf.lower()

def perbaiki_kalimat(huruf):

    # Hapus backslash x dan n
    # mengganti setiap karakter newline (baris baru) dengan spasi (' ')
    huruf = re.sub(r"\\x..", "",huruf)
    huruf = re.sub(r"\n", "",huruf)
    huruf = re.sub('\n',' ',huruf)

    # mengganti setiap kemunculan dua atau lebih spasi berturut-turut dengan satu spasi (' ')
    huruf = re.sub('  +', ' ', huruf)

    # hapus hastag
    huruf = re.sub(r"#+\w*", "#", huruf)

    # hapus karakter selain huruf dan angka
    huruf = re.sub(r"[^a-zA-Z0-9]+", " ", huruf)

    # menghapus kata cc
    huruf = re.sub(r"\bcc\b", "", huruf) 
    
    return huruf

# menghubungkan database
DB = sqlite3.connect('Data_Challenge.db', check_same_thread = False)
# membaca tabel kata Alay
T_kamus = pd.read_sql_query('SELECT * FROM kamusalay', DB)
# membaca tabel abusive
T_kasar = pd.read_sql_query('SELECT * FROM Abusive', DB)

# untuk membuat sebuah kamus (dictionary) dari dua array/list yang berbeda
alay_dict = dict(zip(T_kamus['Kata Alay'], T_kamus['Kata Normal']))

def alay_to_normal(huruf):
    result = []
    for word in huruf.split(' '):
        if word in alay_dict:
            result.append(alay_dict[word])
        else:
            result.append(word)
    return ' '.join(result)

# membaca kolom kata_kasar dari tabel kata_kasar
l_abusive = T_kasar['Kata Abusive'].str.lower().tolist()

def normalize_abusive(huruf):
    list_word = huruf.split()
    return ' '.join([huruf for huruf in list_word if huruf not in l_abusive])

# menjalankan fungsi pembersihan
def text_cleansing(huruf):
    huruf = lowercase(huruf)
    huruf = perbaiki_kalimat(huruf)
    huruf = alay_to_normal(huruf)
    huruf = normalize_abusive(huruf)
    huruf = huruf.replace("gue", "saya")
    return huruf

@swag_from("docs/input_data.yml", methods=['POST'])

@app.route('/input_data', methods=['POST'])
def test():
    
    input_txt = str(request.form["input_data"])
    
    output_txt = text_cleansing(input_txt)

    with sqlite3.connect("Data_Challenge.db") as DB:
        DB.execute('create table if not exists cleansing (text_ori varchar(255), text_clean varchar(255))')
        query_txt = 'insert into cleansing (text_ori , text_clean) values (?,?)'
        val = (input_txt, output_txt)
        DB.execute(query_txt, val)
        DB.commit()

    return_txt = { "input" :input_txt, "output" : output_txt}
    return jsonify (return_txt)

if __name__ == '__main__':
	app.run()