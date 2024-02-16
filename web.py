import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import PyPDF2
import io
import base64
from spacy.lang.en.stop_words import STOP_WORDS
import spacy
from spacy.matcher import Matcher
import pandas as pd

nlp = spacy.load('en_core_web_md')
skill_path = r'C:\Users\Tairo Kageyama\Documents\GitHub\Python-fo-Natural-Language-Processing-main\lab4\Data\skills.jsonl'
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk(skill_path)
nlp.pipe_names

def preprocessing(sentence):
    stopwords    = list(STOP_WORDS)
    doc          = nlp(sentence)
    clean_tokens = []
    
    for token in doc:
        if token.text not in stopwords and token.pos_ != 'PUNCT' and token.pos_ != 'SYM' and \
            token.pos_ != 'SPACE':
                clean_tokens.append(token.lemma_.lower().strip())
                
    return " ".join(clean_tokens)

def get_skills(text):
    
    skills = []
    
    for ent in text.ents:
        if ent.label_ == 'SKILL':
            skills.append(ent.text + ' ')
            
    return skills

def unique_skills(x):
    return list(set(x))

def get_phone_num(sent):
    matcher = Matcher(nlp.vocab)
    pattern = [{"SHAPE": "ddd"},{"ORTH": "-", "OP": "?"},{"SHAPE": "ddd"},{"ORTH": "-", "OP": "?"},{"SHAPE": "dddd"}]
    matcher.add("PHONE_NUMBER", [pattern])
    matches = matcher(sent)

    for match_id, start, end in matches:
        span = sent[start:end]
        result = span.text

        print('a')
        return result
    
def token_words(text):
    doc = nlp(text)
    words = []
    for token in doc:
        words.append(str(token))

    return list(set(words))

df = pd.DataFrame({
            'Skills': [''],
            'Phone': [''],
            'Key Words': ['']
        })

def export_csv(n_clicks):
    if n_clicks is not None:
        # CSV形式でデータフレームを文字列に変換
        csv_string = df.to_csv(index=False, encoding='utf-8')

        # ダウンロードコンポーネントにデータを返す
        return dict(content=csv_string, filename='data.csv')
    else:
        # クリックがない場合はNoneを返す
        return None
output = None
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Upload(
        id='upload-pdf',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select PDF File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
        
    ),
    html.Div(id='output-pdf'),
    html.Button('Export CSV', id='export-csv-button'),
    dcc.Download(id='download-csv')
])

@app.callback(
    [
        Output('output-pdf', 'children'),
        Output('download-csv', 'data')
    ],
    [
        Input('upload-pdf', 'contents'),
        Input('export-csv-button', 'n_clicks')
    ]
)
def update_output(contents, n_clicks):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded_content = base64.b64decode(content_string)

        reader = PyPDF2.PdfReader(io.BytesIO(decoded_content))
        page = reader.pages[0]
        text = page.extract_text()
        text = preprocessing(text)
        text = nlp(text)
        skills = unique_skills(get_skills(text))
        phone = get_phone_num(text)
        words = token_words(text)
        result = {}
        skill_df = ''

        for skill in skills:
            skillN=nlp(skill)
            skill_df += skill + ', '
            sim_words = ' '
            for word in words:
                wordN=nlp(word)
                sim = skillN.similarity(wordN)
                if sim >= 0.7:
                    sim_words += word + ', '
            result[skill] = sim_words
        print(skill_df)
        keyWords=''
        for skill in result.keys():
            keyWords += skill + result[skill] + ', '
        df['Skills']=skill_df
        df['Phone']=phone
        df['Key Words']=keyWords
        return (
            html.Div([
                html.H5('Skills'),
                html.P(skills),
                html.H5('Phone'),
                html.P(phone),
                html.H5('Key Words'),
                html.P(keyWords)
            ], id='output-pdf'),
            export_csv(n_clicks)
        )
            
    else:
        return html.Div('No PDF file uploaded yet.'), None

if __name__ == '__main__':
    app.run_server(debug=True)
