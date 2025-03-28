from flask import Flask, request, render_template, redirect, url_for
from peewee import Model, CharField, IntegerField, SqliteDatabase
import pandas as pd
import plotly.express as px
import os
import logging

app = Flask(__name__)
db = SqliteDatabase('data.db')


class BaseModel(Model):
    class Meta:
        database = db


class DataEntry(BaseModel):
    vecums = CharField()            
    dzimums = CharField()          
    muzika_stradajot = CharField()  
    produktivitate = CharField()    
    muzikas_veids = CharField()     
    skanas_limenis = CharField()    
    koncentracija = CharField()    
    traucejosa_muzika = CharField()
    traucejosi_zanri = CharField(null=True)
    palidz_mierigakam = CharField() 


db.connect()
db.create_tables([DataEntry], safe=True)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            try:
                
                df = pd.read_csv(file, encoding='utf-8', delimiter=';')
               
                df.columns = df.columns.str.strip() 
                
                
                print("CSV failā atrastās kolonnas:", df.columns.tolist())

                
                expected_columns = {
                    "Kāds ir jūsu vecums?",
                    "Kāds ir jūsu dzimums?",
                    "Vai tu klausies mūziku, kad mācies vai strādā?",
                    "Kā tu vērtē savu produktivitāti mācību/darba laikā (bez mūzikas)?",
                    "Kāda veida mūziku tu parasti  klausies mācību/darbu laikā?",
                    "Cik skaļi tu klausies mūziku mācību/ darba laikā?",
                    "Kā mūzikas klausīšanās ietekmē tavu koncentrēšanos?",
                    "Vai ir kāds mūzikas žanrs, kas tev traucē mācībās/darbā?",
                    "Ja uz iepriekšējo jautājumu atbildēji jā, tad kāds/kādi?",
                    "Vai mūzikas klausīšanās tev palīdz justies mierīgākam?"
                }
                
                if not expected_columns.issubset(df.columns):
                    return f"Nederīgs CSV formāts. Atrastas kolonnas: {df.columns.tolist()}.", 400

                DataEntry.delete().execute()

                for _, row in df.iterrows():
                    DataEntry.create(
                        vecums=row["Kāds ir jūsu vecums?"],
                        dzimums=row["Kāds ir jūsu dzimums?"],
                        muzika_stradajot=row["Vai tu klausies mūziku, kad mācies vai strādā?"],
                        produktivitate=row["Kā tu vērtē savu produktivitāti mācību/darba laikā (bez mūzikas)?"],
                        muzikas_veids=row["Kāda veida mūziku tu parasti  klausies mācību/darbu laikā?"],
                        skanas_limenis=row["Cik skaļi tu klausies mūziku mācību/ darba laikā?"],
                        koncentracija=row["Kā mūzikas klausīšanās ietekmē tavu koncentrēšanos?"],
                        traucejosa_muzika=row["Vai ir kāds mūzikas žanrs, kas tev traucē mācībās/darbā?"],
                        traucejosi_zanri=row["Ja uz iepriekšējo jautājumu atbildēji jā, tad kāds/kādi?"],
                        palidz_mierigakam=row["Vai mūzikas klausīšanās tev palīdz justies mierīgākam?"]
                    )

                return redirect(url_for('view_data'))
            except Exception as e:
                logging.error(f"Kļūda CSV apstrādē: {str(e)}")
                return "Neizdevās apstrādāt CSV failu.", 400
    return render_template('upload.html')

@app.route('/secinajumi', methods=['GET', 'POST'])
def secinajumi():
    return render_template('secinajumi.html')
    

@app.route('/data', methods=['GET'])
def view_data():
    filter_gender = request.args.get('dzimums', None)
    filter_music = request.args.get('muzika_stradajot', None)

    query = DataEntry.select()
    if filter_gender:
        query = query.where(DataEntry.dzimums == filter_gender)
    if filter_music:
        query = query.where(DataEntry.muzika_stradajot == filter_music)

    df = pd.DataFrame(list(query.dicts()))

    hist_productivity_plot  = "Pameiģini velveinreiz" 
    hist_concentration_plot = "Pameiģini velveinreiz X2" 
    pie_chart_music_genres  = "Pameiģini velveinreiz x3" 

    if not df.empty:
        fig_productivity = px.histogram(df, x='produktivitate', title='Produktivitātes vērtējums')
        hist_productivity_plot = fig_productivity.to_html(full_html=False)

        fig_concentration = px.histogram(df, x='koncentracija', title='Koncentrācijas ietekme')
        hist_concentration_plot = fig_concentration.to_html(full_html=False)

        fig_pie = px.pie(df, names='muzikas_veids', title='Mūzikas žanru sadalījums')
        pie_chart_music_genres = fig_pie.to_html(full_html=False)

    dzimumi = [entry.dzimums for entry in DataEntry.select(DataEntry.dzimums).distinct()]
    muzika_options = [entry.muzika_stradajot for entry in DataEntry.select(DataEntry.muzika_stradajot).distinct()]

    return render_template('data.html', 
        plot_productivity=hist_productivity_plot if hist_productivity_plot else "", 
        plot_concentration=hist_concentration_plot if hist_concentration_plot else "",
        pie_chart_music_genres=pie_chart_music_genres if pie_chart_music_genres else "",
        dzimumi=dzimumi,
        muzika_options=muzika_options
    )

@app.route('/clear_data', methods=['POST'])
def clear_data():
    try:
        DataEntry.delete().execute()
        return redirect(url_for('view_data'))
    except Exception as e:
        logging.error(f"Kļūda dzēšot datus: {str(e)}")
        return "Neizdevās dzēst datus.", 400

if __name__ == '__main__':
    app.run(debug=True)