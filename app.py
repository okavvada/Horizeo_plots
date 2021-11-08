# flask_web/app.py

from flask import Flask, render_template, request
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sqlite3
import numpy as np
pd.options.mode.chained_assignment = None

app = Flask(__name__)

@app.route('/callback', methods=['POST', 'GET'])
def cb():
    return gm(request.args.get('data'))
   
@app.route('/')
def index():
    return render_template('chartsajax.html')

def gm(project = 'press'):

    print('project =', project)

    conn_output = sqlite3.connect('data/Horizeo.sqlite')
    verbatims_df = pd.read_sql('''SELECT * FROM all_verbatims_df''', conn_output)
    press_df = pd.read_sql('''SELECT * FROM all_press_df''', conn_output)

    press_df = press_df[press_df['text']!='']
    verbatims_df = verbatims_df[verbatims_df['text']!='']

    if project == 'press':
        s = press_df['actors'].str.split('; ').apply(pd.Series, 1).stack()
        s.index = s.index.droplevel(-1)
        s.name = 'actors_names'
        prediction_stack = press_df.join(s)

        prediction_stack_grouped = prediction_stack.groupby(['section', 'actors_names'])

        prediction_stack_grouped_count = prediction_stack_grouped['actors'].count().reset_index().rename(columns={'actors': 'count'})
        prediction_stack_grouped_count = prediction_stack_grouped_count[prediction_stack_grouped_count['actors_names']!='']

        prediction_stack_grouped_topic = prediction_stack.groupby(['section', 'topic_name'])
        prediction_stack_grouped_count_topic = prediction_stack_grouped_topic['actors'].count().reset_index().rename(columns={'actors': 'count'})
        prediction_stack_grouped_count_topic = prediction_stack_grouped_count_topic[prediction_stack_grouped_count_topic['topic_name']!='']

        prediction_stack_grouped_topic_actor = prediction_stack.groupby(['section', 'topic_name', 'actors_names'])
        prediction_stack_grouped_count_topic_actor = prediction_stack_grouped_topic_actor['actors'].count().reset_index().rename(columns={'actors': 'count'})
        prediction_stack_grouped_count_topic_actor = prediction_stack_grouped_count_topic_actor[prediction_stack_grouped_count_topic_actor['actors_names']!='']

        org_count_HORIZEO = prediction_stack_grouped_count[prediction_stack_grouped_count['section'] == 'HORIZEO']

        topic_count_HORIZEO = prediction_stack_grouped_count_topic[prediction_stack_grouped_count_topic['section'] == 'HORIZEO']
        
        org_topic_count_HORIZEO = prediction_stack_grouped_count_topic_actor[prediction_stack_grouped_count_topic_actor['section'] == 'HORIZEO']
        
        org_count_HORIZEO['name'] = np.where(org_count_HORIZEO['count']< 5, 'Other organizations', org_count_HORIZEO['actors_names'])
        
        topic_count_HORIZEO['name'] = np.where(topic_count_HORIZEO['count']< 0, 'Other topic', topic_count_HORIZEO['topic_name'])
        
        specs = [[{'type':'domain'}]]
        fig = make_subplots(rows=1, cols=1, specs=specs)
        fig.add_trace(go.Pie(labels=list(org_count_HORIZEO.name), values=list(org_count_HORIZEO['count']), name="HORIZEO"),
                      1, 1)

        # Use `hole` to create a donut-like pie chart
        fig.update_traces(hole=.3, hoverinfo="label+percent", textposition='inside')

        fig.update_layout(
            height=400, width=900,
            title_text="Actors presence in Press Reviews")


        specs2 = [[{'type':'domain'}]]
        fig2 = make_subplots(rows=1, cols=1, specs=specs)
        fig2.add_trace(go.Pie(labels=list(topic_count_HORIZEO.name), values=list(topic_count_HORIZEO['count']), name="HORIZEO"),
                      1, 1)


        # Use `hole` to create a donut-like pie chart
        fig2.update_traces(hole=.3, hoverinfo="label+percent", textposition='inside')

        fig2.update_layout(
            height=400, width=1000,
            title_text="Topics presence in Press Reviews")

        top10_orgs_HORIZEO = org_count_HORIZEO.sort_values('count',ascending = False).head(15)['actors_names'].values
        org_topic_count_df_HORIZEO_stack_sub = org_topic_count_HORIZEO[org_topic_count_HORIZEO['actors_names'].isin(top10_orgs_HORIZEO)]
        
        fig3 = px.bar(org_topic_count_df_HORIZEO_stack_sub, x="actors_names", y="count", color="topic_name", title="Topics mentioned by top 15 orgs in HORIZEO")
        fig3.update_layout(
                height=600, width=1200,
                title_text="Topics mentioned by top 15 orgs in HORIZEO")
        figures = [fig, fig2, fig3]

    if project == 'verbatims':
        verbatims_df.loc[verbatims_df['org'].isnull(), 'org'] = 'Particuliers'
        all_verbatims_df = verbatims_df[verbatims_df['org'].notnull()]
        all_verbatims_df['new_text'] = all_verbatims_df.groupby(['org', 'city'])['text'].transform(lambda x: ','.join(x))
        all_verbatims_text = all_verbatims_df[['org','city', 'new_text']].drop_duplicates()
        all_verbatims_text['count'] = all_verbatims_text['new_text'].apply(lambda row: len(row))
        prediction_stack_grouped_count = all_verbatims_text.copy()

        prediction_stack_grouped_topic = verbatims_df.groupby(['city', 'topic_name'])
        prediction_stack_grouped_count_topic = prediction_stack_grouped_topic['position'].count().reset_index().rename(columns={'position': 'count'})

        prediction_stack_grouped_topic_actor = verbatims_df.groupby(['city', 'topic_name', 'org'])
        prediction_stack_grouped_count_topic_actor = prediction_stack_grouped_topic_actor['position'].count().reset_index().rename(columns={'position': 'count'})

        org_count_Saucats = prediction_stack_grouped_count[prediction_stack_grouped_count['city'] == 'Saucats']
        org_count_Bordeux = prediction_stack_grouped_count[prediction_stack_grouped_count['city'] == 'Bordeaux']

        org_count_Saucats['orgs'] = np.where(org_count_Saucats['count']< 2300, 'Other organizations', org_count_Saucats['org'])
        org_count_Bordeux['orgs'] = np.where(org_count_Bordeux['count']< 2300, 'Other organizations', org_count_Bordeux['org'])

        topic_count_Saucats = prediction_stack_grouped_count_topic[prediction_stack_grouped_count_topic['city'] == 'Saucats']
        topic_count_Bordeux = prediction_stack_grouped_count_topic[prediction_stack_grouped_count_topic['city'] == 'Bordeaux']

        org_topic_count_Saucats = prediction_stack_grouped_count_topic_actor[prediction_stack_grouped_count_topic_actor['city'] == 'Saucats']
        org_topic_count_Bordeux = prediction_stack_grouped_count_topic_actor[prediction_stack_grouped_count_topic_actor['city'] == 'Bordeaux']

        
        specs = [[{'type':'domain'}, {'type':'domain'}]]
        fig = make_subplots(rows=1, cols=2, specs=specs)
        fig.add_trace(go.Pie(labels=list(org_count_Saucats.orgs), values=list(org_count_Saucats['count']), name="Saucats"),
                      1, 1)
        fig.add_trace(go.Pie(labels=list(org_count_Bordeux.orgs), values=list(org_count_Bordeux['count']), name="Bordeaux"),
              1, 2)

        # Use `hole` to create a donut-like pie chart
        fig.update_traces(hole=.30, hoverinfo="label+percent", textposition='inside')

        fig.update_layout(
            height=700, width=1200,
            title_text="Actors presence in Verbatims",
            annotations=[dict(text='Saucats', x=0.15, y=1.07, font_size=20, showarrow=False),
                     dict(text='Bordeaux', x=0.92, y=1.07, font_size=20, showarrow=False),
                 ])


        specs2 = [[{'type':'domain'},  {'type':'domain'}]]
        fig2 = make_subplots(rows=1, cols=2, specs=specs)
        fig2.add_trace(go.Pie(labels=list(topic_count_Saucats.topic_name), values=list(topic_count_Saucats['count']), name="Saucats"),
              1, 1)
        fig2.add_trace(go.Pie(labels=list(topic_count_Bordeux.topic_name), values=list(topic_count_Bordeux['count']), name="Bordeaux"),
              1, 2)


        # Use `hole` to create a donut-like pie chart
        fig2.update_traces(hole=.30, hoverinfo="label+percent", textposition='inside')

        fig2.update_layout(
            height=700, width=1000,
            title_text="Topics presence in Verbatims",
            annotations=[dict(text='Saucats', x=0.15, y=1.07, font_size=20, showarrow=False),
                 dict(text='Bordeaux', x=0.92, y=1.07, font_size=20, showarrow=False),
                ])

        top10_orgs_Saucats = org_count_Saucats.sort_values('count',ascending = False).head(15)['org'].values
        org_topic_count_df_Saucats_stack_sub = org_topic_count_Saucats[org_topic_count_Saucats['org'].isin(top10_orgs_Saucats)]

        fig3 = px.bar(org_topic_count_df_Saucats_stack_sub, x="org", y="count", color="topic_name", title="Topics mentioned by top 15 orgs in Saucats")
        fig3.update_layout(
                height=700, width=1200,
                title_text="Topics mentioned by top 15 orgs in Saucats")

        top10_orgs_Bordeaux = org_count_Bordeux.sort_values('count',ascending = False).head(15)['org'].values
        org_topic_count_df_Bordeaux_stack_sub = org_topic_count_Bordeux[org_topic_count_Bordeux['org'].isin(top10_orgs_Bordeaux)]
        fig4 = px.bar(org_topic_count_df_Bordeaux_stack_sub, x="org", y="count", color="topic_name", title="Topics mentioned by top 15 orgs in Bordeaux")
        fig4.update_layout(
           height=700, width=1200,
                title_text="Topics mentioned by top 15 orgs in Bordeaux")

        figures = [fig, fig2, fig3, fig4]


    return  json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)