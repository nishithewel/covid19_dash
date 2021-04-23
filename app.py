# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 10:48:50 2020

@author: ACER
"""

#%%


# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 12:35:29 2020

@author: ACER
"""


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input
from dash.dependencies import Output
import pandas as pd




#%%
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('COVID19LYN-secret.json', scope)
client = gspread.authorize(creds)
sht = client.open('Covid-19 Sri Lanka')

#%%


df_pop = pd.read_csv('population data.csv')
df_pop.rename(columns={'2018 [YR2018]':'2018','Country Name':'location'},inplace=True)

#%%
# def df_join_clean(sheet_name,csv):
SL_sheet = sht.worksheet('Sheet1').get()

df_SL = pd.DataFrame(SL_sheet,columns=['date','location','variable','value'])
df_SL.value = df_SL.value.astype('int64')
    
    
    # df_SL.set_index('date',inplace=True,drop=True)
    
    # df_SL= df_SL.fillna(0).astype('int32')
    
    # df_global = pd.read_csv(csv)
    
   
    # df_global.drop('Sri Lanka',inplace=True,axis=1)
    
    # df_global['date'] = pd.to_datetime(df_global['date'])
    
    
    
    # df_global.set_index('date',inplace=True,drop=True)
    # df_global = df_global.fillna(0).astype('int32')
    
    # df=  df_SL.merge(df_global,how='outer',left_index=True,right_index=True)
    # return df

def per_1000(x):
    try:
        return x.divide(df_pop.loc[df_pop['Country Name']==country_name]['2018'].item(),axis=0)*1000
    except:
        pass

#%%
# df = df_join_clean('Sheet1','https://covid.ourworldindata.org/data/ecdc/total_cases.csv')
df_untidy = pd.read_csv('https://covid.ourworldindata.org/data/ecdc/full_data.csv') 



df = df_untidy.melt(id_vars=['date','location'])
df = df.loc[(df.location != 'Sri Lanka') | (df.variable!='total_cases') ]
df = df.append(df_SL)


df_untidy['date'] = pd.to_datetime(df_untidy['date'])
df_untidy.set_index('date',inplace=True)



 #this is a hack , fix later

df['date'] = pd.to_datetime(df['date'])
df.set_index('date',inplace=True)




date_epoch = (df.index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
dates = df.index.strftime('%m-%d').to_list()



#%% district case breakdown

import json
# with urlopen('data\\LKA_adm1.geojson') as response:
with open("LKA_adm1.json") as h:
    json = json.load(h)
    
district_cases = sht.worksheet('dist_num').get()
df_dist = pd.DataFrame(district_cases,columns=['District','Cases'])
df_dist.Cases = df_dist.Cases.astype('int32')
df_dist.District= df_dist.District.str.lower().str.capitalize()



import plotly.express as px

#creates a plotly map 
fig = px.choropleth(df_dist, geojson=json, color="Cases",
                    locations="District", featureidkey="properties.NAME_1",
                    projection="mercator"
                   )

fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(title_text = '2011 US Agriculture Exports by State')
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()



#%% this is the dash app part

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']



app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

countries = df.location.unique()

# style={'backgroundColor': colors['background']},children=


def serve_layout():
    return html.Div([
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id='country-names',
                        options=[{'label':i, 'value':i} for i in countries],
                        value = ['Sri Lanka','Singapore'],
                        multi=True),
                   ],className='six columns'
                    ),
                html.Div([
                    dcc.Dropdown(
                        id='var-type',
                        options=[{'label':i, 'value':i} for i in df.variable.unique()],
                        value='total_cases')
                    ],className="six columns"
                    ),
                
    
                                                
                           
                        #fix for multi and adjsut width
                dcc.RadioItems(
                        id='yaxis-type',
                        options=[{'label':i, 'value':i} for i in ['Linear','Logarithmic']],
                        value=  'Linear',
                        labelStyle={'display': 'inline-block'},
                        )
                    ]),
                html.Div([
                    html.Div(
                        [dcc.Graph(
                        id='indicator-graph')
                        ],style={'width': '49%', 'display': 'inline-block'}
                        ),
                    html.Div([
                        dcc.Graph(
                        id='exp-graph')
                        ],style={'width': '49%', 'display': 'inline-block'}
                        )
                   
                    
                    ]),
                
                
                    html.Div([
                        dcc.Slider(
                            id='day--year',
                            min = date_epoch.min(),
                            max= date_epoch.max(),
                            value= date_epoch.max(),
                            marks={ix : {'label': date ,
                                          'style':{'height':'50px',
                                                   'writing-mode': 'vertical-rl'}}
                                    for ix,date in zip(date_epoch,dates)},
                            step=None)
                            ],style={'height':'100px'}
                            ),
                                   
                    
                        
                
            
            html.Div([
                html.Div([
                    
                    html.Div([
                        dcc.Dropdown(
                            id='total-percentage',
                            options=[{'label':i, 'value':i} for i in ['Total Number','% of Population']],
                            value = 'Total Number'
                        )]
                        ,style={'width': '49%', 'display': 'inline-block'}
                    ),
                    dcc.Graph(
                        id='trajectory-graph'),
                    html.Div([
                    dcc.Slider(
                        id ='day--epidemic',
                        min=0,
                        max=100,
                        value=50,
                        marks={str(day):str(day) for day in range(0,100,10)})
                    ],style={'width': '49%', 'display': 'inline-block'}
                        ),
                    html.Div([
                        dcc.Slider(
                            id='case-threshold',
                            min = 10,
                            max= 1000,
                            value= 10,
                            marks={str(10**i):str(10**i) for i in range(1,4)},
                            step=None,
                            updatemode='drag'
                            )
                                                    
                    ],style={'width': '49%', 'display': 'inline-block'}
                        )
                    ],style={'width': '49%', 'padding': '0px 20px 20px 20px'}
                    , className="six columns"),
                html.Div([
                    dcc.Graph(
                        id='district-map',
                        figure=fig)
                    ],style={'width': '40%', 'padding': '0px 20px 20px 20px'}
                    , className="six columns")
                # ,
                #   html.Div([
                # dcc.Graph(
                #     id='population-graph')
                # ])
            
                
            ])
            
          
                
                    
                
        
        ])
app.layout = serve_layout
# ,'text-orientation': 'upright'
@app.callback(
    Output('indicator-graph', 'figure'),
    [Input('country-names','value'),
    Input('yaxis-type','value'),
    Input('day--year','value'),
    Input('var-type','value')]
    )

def update_graph(country_names,yaxis_type,dateepoch,var_type):
    dff = df.loc[(df.index <= pd.to_datetime(dateepoch,unit='s')) & (df.variable==var_type)]
    df_list = [(dff.loc[dff['location']==country_name],country_name) for country_name in country_names]
    if df.variable.all()=='new_cases':
        return{
            'data':
                    [dict(
                    x=df.index,
                    y=df.value.ewm(span=7,adjust=False).mean(),
                    name=country_name,
                    mode='lines',
                    marker={
                        'size': 15,
                        'opacity': 0.5,
                        'line': {'width': 0.5, 'color': 'white'}
                        }
                ) for df,country_name in df_list],
            'layout':dict(
                yaxis={
                    'title':f'{var_type}',
                    'type': 'linear' if yaxis_type == 'Linear' else 'log'},
                margin={'l': 100, 'b': 40, 't': 10, 'r': 100},
                hovermode='closest',
                transition= {
                    'duration': 500,
                    'easing': 'cubic-in-out'}
                )
            }
    else:
        return{
            'data':
                    [dict(
                    x=df.index,
                    y=df.value,
                    name=country_name,
                    mode='lines',
                    marker={
                        'size': 15,
                        'opacity': 0.5,
                        'line': {'width': 0.5, 'color': 'white'}
                        }
                ) for df,country_name in df_list],
            'layout':dict(
                yaxis={
                    'title':f'{var_type}',
                    'type': 'linear' if yaxis_type == 'Linear' else 'log'},
                margin={'l': 100, 'b': 40, 't': 10, 'r': 100},
                hovermode='closest',
                transition= {
                    'duration': 500,
                    'easing': 'cubic-in-out'}
                )
            }
@app.callback(
    Output('trajectory-graph','figure'),
    [Input('country-names','value'),
     Input('yaxis-type','value'),
     Input('day--epidemic','value'),
     Input('case-threshold','value'),
     Input('total-percentage','value'),
     Input('var-type','value')]    
    )
def update_trajectory(country_names,yaxis_type,days_epidemic,threshold_case_number,total_percentage,var_type):
    # THRESHOLD_CASE_NUMBER = 10
    #creates a list of dfs with traj data 
    # if value== '% of Population':
    #     df_pop_perc = df_pop_adjusted
    # else:
    
    
    
    traj_dfs= []
    for country_name in country_names:
        traj_df = df.loc[(df.value>= threshold_case_number)
                              & (df.variable==var_type) & (df.location==country_name)].reset_index()
        traj_df['day_count'] = (traj_df.date - traj_df.date[0]).dt.days
        if total_percentage=='% of Population':
            traj_df2 = traj_df.loc[traj_df.day_count <= days_epidemic]
            traj_dff = df_pop.merge(traj_df2)
            traj_dff.value = traj_dff.value.divide(traj_dff['2018'])
            
        else:
            traj_dff = traj_df.loc[traj_df.day_count <= days_epidemic]
            
        # traj_dff= trajdf2.apply(lambda x : per_1000(x),axis=0)

        
        traj_dfs.append(traj_dff)

    return{
        'data':[dict(
            x=df.day_count,
            y=df.value,
            name=country_name,
            mode='lines+markers',
            
                )for country_name,df in zip(country_names,traj_dfs)],
            'layout':dict(
            xaxis={
                'title':f'Days since {threshold_case_number} cases confirmed'
                },
            yaxis={
                'title':f'{var_type}',
                'type': 'linear' if yaxis_type == 'Linear' else 'log'},
            margin={'l': 100, 'b': 40, 't': 10, 'r': 100},
            hovermode='closest',
            transition= {
                'duration': 500,
                'easing': 'cubic-in-out'}
            )
         }

#%%
@app.callback(
    Output('exp-graph','figure'),
    [Input('country-names','value'),
     Input('yaxis-type','value'),
     Input('day--year','value')
     ]    
    )
def update_log_exp(country_names,yaxis_type,dateepoch):
    
    exp_dfs= []
    for country_name in country_names:
        exp_df = df_untidy.loc[(df_untidy.index <= pd.to_datetime(dateepoch,unit='s')) & 
                               (df_untidy.location==country_name) &
                               (df_untidy.total_cases>=75)] #100 is the threshhold num cases
        exp_df['new_cases_smooth'] = exp_df.new_cases.ewm(span=7,adjust=False).mean()
        exp_dfs.append(exp_df)

    return{
        'data':[dict(
            x=df.total_cases,
            y=df.new_cases_smooth,
            name=country_name,
            mode='lines'
            
                )for country_name,df in zip(country_names,exp_dfs)],
            'layout':dict(
            xaxis={
                'title':'Total cases',
                'type': 'linear' if yaxis_type == 'Linear' else 'log' #yes i know xaxis type 
                },
            yaxis={
                'title':'New Cases  confirmed over 7 days',
                'type': 'linear' if yaxis_type == 'Linear' else 'log'
                },
            margin={'l': 100, 'b': 40, 't': 10, 'r': 100},
            hovermode='closest',
            transition= {
                'duration': 500,
                'easing': 'cubic-in-out'
                }
            )
         }




if __name__ == '__main__':
    app.run_server()
        
        
        
        
        
    
    
    
    
    
    
