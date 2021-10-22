## importing required libraries

import get_connected ## custom package

import warnings
warnings.filterwarnings('ignore')

import dash 
from dash import dash_table
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.exceptions import PreventUpdate

import pandas as pd


## db credentials

host="mysql-prod-db1-rds.csxffbq6aqlg.us-west-2.rds.amazonaws.com"
port=4475
user="RZcE1F37"
passwd="1F3737"
database='Syspro7RefV1_1009372'


## getting CFO dashboard data

main_db = get_connected.get_connection(host, port, user, passwd, database)
conn_check = get_connected.check_connection(main_db)

mycursor = main_db.cursor()

## Collecting  data 
CFO_query = 'select year(Fiscal_Date) as YEAR, month(Fiscal_Date) as MONTH, Company_Id as COMPANY_NAME, Ledger_Section as LEDGER_SECTION, \
            round(sum(NetSales), 2) as NET_SALES, round(sum(GrossMargin), 2) as GROSS_MARGIN, round(sum(GrossMargin_Percent), 2) as GROSS_MARGIN_PERCENT, round(sum(AccountReceivables), 2) as AR, \
            round(sum(AccountPayables), 2) as AP, \
            round(sum(ReturnOnAssets), 2) as RETURN_ON_ASSETS, round(sum(ReturnOnEquity), 2) as RETURN_ON_EQUITY, \
            round(sum(WorkingCapital), 2) as CAPITAL, round(sum(WorkingRatio), 2) as CAPITAL_RATIO, \
            round(sum(DebtRatio), 2) as DEBT_RATIO, round(sum(DebtToEquityRatio), 2) as DEBT_TO_EQUITY_RATIO, \
            round(sum(DaysInventoryOutstanding), 2) as DIO, round(sum(DaysSalesOutstanding), 2) as DSO, round(sum(DaysPayableOutstanding), 2) as DPO, \
            round(sum(CashToCashCycle), 2) as CASH_TO_CASH_CYCLE, round(sum(Expenses), 2) as EXPENSES, round(sum(OperatingProfit_Percent), 2) as OPERATING_PROFIT_PERCENT, \
            round(sum(COGS), 2) as COGS, round(sum(CurrentAssets), 2) as CURRENT_ASSETS, round(sum(CurrentLiabilities), 2) as CURRENT_LIABILITIES, \
            round(sum(WorkingRatio), 2) as WORKING_RATIO, round(sum(QuickRatio), 2) as QUICK_RATIO, \
            round(sum(Assets), 2) as ASSETS, round(sum(Liabilities), 2) as LIABILITIES \
            from DM_Financial_Overview \
            where year(Fiscal_Date)  IS NOT NULL \
            group by YEAR, MONTH, COMPANY_NAME, LEDGER_SECTION '

mycursor.execute(CFO_query)
CFO_data = mycursor.fetchall()

mycursor.close()
main_db.close()
conn_check = get_connected.check_connection(main_db)

## hard coding col names 
col_names = ['YEAR', 'MONTH', 'COMPANY_NAME', 'LEDGER_SECTION', 'NET_SALES', 'GROSS_MARGIN', 'GROSS_MARGIN_PERCENT', 'AR', 'AP', 'RETURN_ON_ASSETS', 'RETURN_ON_EQUITY', 'CAPITAL', 'CAPITAL_RATIO', 'DEBT_RATIO', 
             'DEBT_TO_EQUITY_RATIO', 'DIO', 'DSO', 'DPO', 'CASH_TO_CASH_CYCLE', 'EXPENSES', 'OPERATING_PROFIT_PERCENT', 'COGS', 'CURRENT_ASSETS', 'CURRENT_LIABILITIES', 'WORKING_RATIO', 
             'QUICK_RATIO', 'ASSETS', 'LIABILITIES']

## converting our query results into df
data_for_df = [record for record in CFO_data] ## list of tuples for creating dataframe

# creating df 
main_df = pd.DataFrame(data_for_df, columns=col_names)

## filling all the null values with 0
main_df = main_df.fillna(0)

## combining year and month col
def combine(year, month):
    return(str(year)+'-'+str(month))

new_dates = main_df.apply(lambda x: combine(x['YEAR'], x['MONTH']), axis=1)

main_df['YEAR_MONTH'] = new_dates

## creating company branch data for default charts

comp_branch_data = main_df[(main_df['COMPANY_NAME'] == 'EDU1') & (main_df['LEDGER_SECTION'] == 'East')]


## dual charts 

def get_dual_charts(data, measure_one, measure_one_name, measure_two, measure_two_name,  measure_three, measure_three_name, yaxis_1, yaxis_2):
    '''
        iputs company branch data and returns charts related to it
    '''

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=data.YEAR_MONTH, y=data[measure_one], name=measure_one_name, marker=dict(color='#0e7e75')),
        secondary_y=False,
    )

    # Add traces
    fig.add_trace(
        go.Bar(x=data.YEAR_MONTH, y=data[measure_two], name=measure_two_name, marker=dict(color='#b3700d')),
        secondary_y=False,
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_three], name=measure_three_name, mode='lines+markers', marker=dict(size=8, color='#767f92')),
        secondary_y=True,
    )

    fig.update_yaxes(title_text=yaxis_1, secondary_y=False)
    fig.update_yaxes(title_text=yaxis_2, secondary_y=True)
    fig.update_xaxes(showgrid=True, gridwidth=0.5)

    fig.update_layout(
        # title_text="Gross Margin Over Time",
        xaxis_title="Year Month",
        hovermode="x unified",
        xaxis = dict(
            tickmode = 'array',
            tickvals = data.YEAR_MONTH,
            ticktext = data.YEAR_MONTH
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation='h',
            x=0,
            y=1),

    )


    return fig

def get_ar_donut(data, year, month):
    '''
        inputs company branch data and returns donut chart
    '''

    last_month =  month - 1
    # calculating last month data for AR
    last_month_ar = data[(data['YEAR'] == year) & (data['MONTH'] == last_month)].AR.tolist()
    if len(last_month_ar) == 0:
        last_month_ar = 0
    else:
        last_month_ar = float(last_month_ar[0])

    ## calculating last year data for AR

    last_year =  year - 1
    last_year_ar = data[data['YEAR'] == last_year].AR.tolist()
    if len(last_year_ar) == 0:
        last_year_ar = 0
    else:
        last_year_ar = float(last_year_ar[0])

        
    current_ar_balance = data[(data['YEAR'] == year) & (data['MONTH'] == month)].AR.tolist()
    if len(current_ar_balance) == 0:
        current_ar_balance = 0
    else:
        current_ar_balance = float(current_ar_balance[0])

    ### creating figure
    labels = ["Balance", "Last Month", "Last Year"]

    fig = go.Figure(
            go.Pie(labels=labels, values=[current_ar_balance, last_month_ar, last_year_ar])
        )

    # Use `hole` to create a donut-like pie chart
    fig.update_traces(hole=.4, hoverinfo="label+value", textinfo="value", textfont_size=15)

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(
                orientation='v',
                x=0,
                y=1),
        # Add annotations in the center of the donut pies.
        annotations=[dict(text='AR', x=0.5, y=0.5, font_size=35, showarrow=False)])


    return fig

def get_ap_donut(data, year, month):
    '''
        inputs company branch data and returns donut chart
    '''
    ## calculating last month data for AP
    last_month_ap = data[(data['YEAR'] == year) & (data['MONTH'] == month-1)].AP.tolist()
    if len(last_month_ap) == 0:
        last_month_ap = 0
    else:
        last_month_ap = float(last_month_ap[0])

    ## calculating last year data for AP
    last_year_ap = data[data['YEAR'] == year-1].AP.tolist()
    if len(last_year_ap) == 0:
        last_year_ap = 0
    else:
        last_year_ap = float(last_year_ap[0])

    current_ap_balance = data[(data['YEAR'] == year) & (data['MONTH'] == month)].AP.tolist()
    if len(current_ap_balance) == 0:
        current_ap_balance = 0
    else:
        current_ap_balance = float(current_ap_balance[0])

    ### creating figure
    labels = ["Balance", "Last Month", "Last Year"]

    fig = go.Figure(
            go.Pie(labels=labels, values=[current_ap_balance, last_month_ap, last_year_ap])
        )

    # Use `hole` to create a donut-like pie chart
    fig.update_traces(hole=.4, hoverinfo="label+value", textinfo="value", textfont_size=15)

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(
                orientation='v',
                x=0,
                y=1),
        # Add annotations in the center of the donut pies.
        annotations=[dict(text='AP', x=0.5, y=0.5, font_size=35, showarrow=False)])
    

    return fig


def get_four_charts(data, measure_one, name_one, measure_two, name_two, measure_three, name_three, measure_four, name_four, y_1, y_2):
    '''
        inputs company branch data and returns 4 variables chart
    '''

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=data.YEAR_MONTH, y=data[measure_one], name=name_one, marker=dict(color='LightSkyBlue')),
        secondary_y=False,
    )

    # Add traces
    fig.add_trace(
        go.Bar(x=data.YEAR_MONTH, y=data[measure_two], name=name_two, marker=dict(color='LightGreen')),
        secondary_y=False,
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_three], name=name_three, mode='lines+markers', marker=dict(size=8, color='Brown')),
        secondary_y=True,
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_four], name=name_four, mode='lines+markers', marker=dict(size=8, color='#184f86', symbol="cross")),
        secondary_y=True,
    )

    fig.update_yaxes(title_text=y_1, secondary_y=False)
    fig.update_yaxes(title_text=y_2, secondary_y=True)
    fig.update_xaxes(showgrid=True, gridwidth=0.5)

    fig.update_layout(
        # title_text="Liquidity Ratios Over Time",
        xaxis_title="Year Month",
        hovermode="x unified",
        xaxis = dict(
            tickmode = 'array',
            tickvals = data.YEAR_MONTH,
            ticktext = data.YEAR_MONTH
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation='h',
            x=0,
            y=1),
        
    )
    

    return fig

def get_four_line_plots(data, measure_one, name_one, measure_two, name_two, measure_three, name_three, measure_four, name_four, y_1):
    
    ## plotting dual charts 

    fig = make_subplots(specs=[[{}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_one], name=name_one,  mode='lines+markers', marker=dict(size=8, symbol ='square', color="#0e7e75"))
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_two], name=name_two,  mode='lines+markers', marker=dict(size=8, symbol ='diamond', color="Blue"))
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_three], name=name_three, mode='lines+markers', marker = dict(size=8, symbol = 'circle-open', color="#ae0032"))
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_four], name=name_four, mode='lines+markers', marker = dict(size=8, symbol = 'cross', color="#b3700d"))
    )

    fig.update_yaxes(title_text=y_1)
    # fig.update_yaxes(title_text="Margin (%)", secondary_y=True)
    fig.update_xaxes(showgrid=True, gridwidth=0.5)

    fig.update_layout(
        # title_text="Cash To Cash Cycle Overtime",
        xaxis_title="Year Month",
        hovermode="x unified",
        xaxis = dict(
            tickmode = 'array',
            tickvals = data.YEAR_MONTH,
            ticktext = data.YEAR_MONTH
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation='h',
            x=0,
            y=1),

    )

    return fig


def get_two_line_plots(data, measure_one, name_one, measure_two, name_two, y_1):
    # plotting dual charts 

    fig = make_subplots(specs=[[{}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_one], name=name_one, mode='lines+markers', marker = dict(size=8, symbol = 'circle-open'))
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=data.YEAR_MONTH, y=data[measure_two], name=name_two, mode='lines+markers', marker = dict(size=8, symbol = 'square'))
    )

    fig.update_yaxes(title_text=y_1)
    # fig.update_yaxes(title_text="Margin (%)", secondary_y=True)
    fig.update_xaxes(showgrid=True, gridwidth=0.5)

    fig.update_layout(
        # title_text="Cash To Cash Cycle Overtime",
        xaxis_title="Year Month",
        hovermode="x unified",
        xaxis = dict(
            tickmode = 'array',
            tickvals = data.YEAR_MONTH,
            ticktext = data.YEAR_MONTH
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation='h',
            x=0,
            y=1),

    )

    return fig


## initializing dash app

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
server = app.server

app.layout = dbc.Container([
    ## first row
    dbc.Row(
        dbc.Col(html.H1("Chief Financial Officer", className="text-center mt-3 mb-5", style={"font-size":"50px", "font-family": "Georgia, serif"}), width=12),
    ), 

    ## second row
    dbc.Row(
        [
            dbc.Col(
                [
                    html.H6("Company Name", className="font-weight-bold text-left mt-2", style={"font-size":"16px", "color":"#4c1e30", "font-family": "Georgia, serif"}),
                    dcc.Dropdown(id="company_drpdwn", multi=False, value='',
                    options=[{'label': x, 'value': x} for x in main_df.COMPANY_NAME.unique()], placeholder='Select Company', className="mt-2 shadow")
                ], width=2), 

            dbc.Col(
                [
                    html.H6("Ledger Section Name", className="font-weight-bold text-left mt-2", style={"font-size":"16px", "color":"#4c1e30", "font-family": "Georgia, serif"}),
                    dcc.Dropdown(id="ledger_drpdwn", multi=False, value='',
                    options=[{'label': x, 'value': x} for x in main_df.LEDGER_SECTION.unique()], placeholder='Select Ledger', className="mt-2 shadow")
                ], width=2),

            dbc.Col(
                [
                    html.H6("Year", className="font-weight-bold text-left mt-2", style={"font-size":"16px", "color":"#4c1e30", "font-family": "Georgia, serif"}),
                    dcc.Dropdown(id="year_drpdwn", multi=False, value='',
                    options=[{'label': x, 'value': x} for x in main_df.YEAR.unique()], placeholder='Select Year', className="mt-2 shadow")
                ], width=1),

            dbc.Col(
                [
                    html.H6("Month", className="font-weight-bold text-left mt-2", style={"font-size":"16px", "color":"#4c1e30", "font-family": "Georgia, serif"}),
                    dcc.Dropdown(id="month_drpdwn", multi=False, value='',
                    options=[{'label': x, 'value': x} for x in main_df.MONTH.sort_values().unique()], placeholder='Select Month', className="mt-2 shadow")
                ], width=1),

        ], className="mb-4 ml-3 mr-3 rounded ", justify='start', style={"background-color": "#c0c6fb", "height": "100px", "border": "1px solid"}),

    
    ## third row (adding cards)
    dbc.Row(
        [   ## first card
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6('PERFORMANCE', style={"font-size":"22px",  "color":"#4c1e30", "background-color": "#c0c6fb", "font-family": "Georgia, serif"}, 
                                            className="card-title font-weight-bold card-header rounded"),
                                    ## first value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Net Sales:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-5"), style={"margin-left":"80px"}), 
                                            dbc.Col(html.H6(id='net_sales_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"30px"}),
                                        ]

                                    , no_gutters=True),

                                    ## second value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Gross Margin:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-2"), style={"margin-left":"85px"}), 
                                            dbc.Col(html.H6(id='gross_margin_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"35px"}),
                                        ]

                                    , no_gutters=True),

                                    # # third value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Operating Profit:", style={"font-size":"20px", "color":"black"}, className="mt-3"), style={"margin-left":"75px"}), 
                                            dbc.Col(html.H6(id='operating_profit_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"25px"}),
                                        ]

                                    , no_gutters=True),
                                
                                ], className="text-center")
                        
                        ], style={"height": "250px"}, className="rounded shadow", outline=True)
                ], width=3),
            
            ## second card
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6('ACTIVITY', style={"font-size":"22px",  "color":"#4c1e30", "background-color": "#c0c6fb", "font-family": "Georgia, serif"}, 
                                                className="card-title font-weight-bold card-header rounded"),
                                    ## first value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("AR:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-4"), style={"margin-left":"110px"}), 
                                            dbc.Col(html.H6(id='ar_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"90px"}),
                                        ]

                                    , no_gutters=True),

                                    ## second value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("AP:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-4"), style={"margin-left":"110px"}), 
                                            dbc.Col(html.H6(id='ap_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"90px"}),
                                        ]

                                    , no_gutters=True),

                                    # third value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Cash to Cash Cycle:", style={"font-size":"20px", "color":"black"}, className="mt-3"), style={"margin-left":"25px"}), 
                                            dbc.Col(html.H6(id='ctc_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"15px"}),
                                        ]

                                    , no_gutters=True),
                                
                                ], className="text-center")
                        
                        ], style={"height": "250px"}, className="rounded shadow", outline=True)
                ], width=3),

            ## third card
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6('PROFITABILITY', style={"font-size":"22px",  "color":"#4c1e30", "background-color": "#c0c6fb", "font-family": "Georgia, serif"}, 
                                                className="card-title font-weight-bold card-header rounded"),
                                    ## first value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Return On Assets:", style={"font-size":"20px", "color":"black"}, className="mt-4 ml-2"), style={"margin-left":"50px"}), 
                                            dbc.Col(html.H6(id='roa_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-4"), style={"margin-right":"2px"}),
                                        ]

                                    , no_gutters=True),

                                    ## second value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Return On Equity:", style={"font-size":"20px", "color":"black"}, className="mt-4 ml-2"), style={"margin-left":"50px"}), 
                                            dbc.Col(html.H6(id='roe_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-4"), style={"margin-right":"2px"}),
                                        ]

                                    , no_gutters=True),
                                
                                ], className="text-center")
                        
                        ], style={"height": "250px"}, className="rounded shadow", outline=True)
                ], width=3),

            
            # fourth card
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6('LIQUIDITY', style={"font-size":"22px",  "color":"#4c1e30", "background-color": "#c0c6fb", "font-family": "Georgia, serif"}, 
                                                className="card-title font-weight-bold card-header rounded"),
                                    ## first value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("WORKING CAPITAL:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-2"), style={"margin-left":"20px"}), 
                                            dbc.Col(html.H6(id='working_cap_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"2px"}),
                                        ]

                                    , no_gutters=True),

                                    ## second value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("WC RATIO:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-4"), style={"margin-left":"78px"}), 
                                            dbc.Col(html.H6(id='working_cap_ratio_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"58px"}),
                                        ]

                                    , no_gutters=True),

                                    # third value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("QUICK RATIO:", style={"font-size":"20px", "color":"balck"}, className="mt-3 ml-2"), style={"margin-left":"70px"}), 
                                            dbc.Col(html.H6(id='quick_ratio_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"48px"}),
                                        ]

                                    , no_gutters=True),
                                
                                ], className="text-center")
                        
                        ], style={"height": "250px"}, className="rounded shadow", outline=True)
                ], width=3),

        ], className="mb-4 ml-1 mr-1", justify='start'),

    
    ## fourth row (final card)
    dbc.Row(
            # fifth card
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6('LEVERAGE', style={"font-size":"22px",  "color":"#4c1e30", "background-color": "#c0c6fb", "font-family": "Georgia, serif"}, 
                                                className="card-title font-weight-bold card-header rounded"),
                                    ## first value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Debt Ratio:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-5"), style={"margin-left":"190px"}), 
                                            dbc.Col(html.H6(id='debt_ratio_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"180px"}),
                                        ]

                                    , no_gutters=True),

                                    ## second value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Debt To Equity Ratio:", style={"font-size":"20px", "color":"black"}, className="mt-3 ml-5"), style={"margin-left":"110px"}), 
                                            dbc.Col(html.H6(id='de_ratio_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"100px"}),
                                        ]

                                    , no_gutters=True),

                                    # # third value in the card
                                    dbc.Row(
                                        [
                                            dbc.Col(html.H6("Long Term Debt to Equity:", style={"font-size":"20px", "color":"balck"}, className="mt-3 ml-5"), style={"margin-left":"62px"}), 
                                            dbc.Col(html.H6(id='long_term_de_card', children="0", style={"font-size":"20px", "color":"black"}, className="text-left font-weight-bold mt-3"), style={"margin-right":"50px"}),
                                        ]

                                    , no_gutters=True),
                                
                                ], className="text-center")
                        
                        ], style={"height": "250px"}, className="rounded shadow", outline=True)
                ], width=5),

            className="mb-4 ml-1 mr-1", justify='center'), 
    
    ## fifth row (gross margin chart and donut charts)
    dbc.Row([
        dbc.Col(
            [
                html.H6("Gross Margin Over Time", className="font-weight-bold text-center mt-5", style={"font-size":"16px", "font-family": "Georgia, serif"}),
                dcc.Graph(id='gross_margin_ot', figure=get_dual_charts(comp_branch_data, "NET_SALES", "Net Sales", "COGS", "COGS", "GROSS_MARGIN_PERCENT", "Gross Margin (%)", "Amount", "Margin (%)"), className="shadow rounded", 
                config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True 
                })
        ], width=8),

        dbc.Col(
            [
                # html.H6("AR & AP", className="font-weight-bold text-center text-secondary mt-5", style={"font-size":"16px"}),
                dcc.Graph(id='ar_donut_chart', figure=get_ar_donut(comp_branch_data, 2019, 11), className="shadow rounded", 
                config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True 
                }, style={"margin-top":"76px"})

        ], width=4)

    ]), 

    ## sixth row (operating profit chart)
    dbc.Row([
        dbc.Col(
            [
                html.H6("Operating Profit Over Time", className="font-weight-bold text-center mt-5", style={"font-size":"16px", "font-family": "Georgia, serif"}),
                dcc.Graph(id='operating_profit_ot', figure=get_dual_charts(comp_branch_data, "GROSS_MARGIN", "Gross Margin", "EXPENSES", "Expenses", "OPERATING_PROFIT_PERCENT", "Operating Profit (%)", "Amount", "Profit (%)")
                            , className="shadow rounded", 
                config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True 
                })
        ], width=8),

        dbc.Col(
            [
                dcc.Graph(id='ap_donut_chart', figure=get_ap_donut(comp_branch_data, 2019, 11), className="shadow rounded", 
                config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True 
                }, style={"margin-top":"76px"})

        ], width=4)
    
    ]), 
    
    ## seventh row (Liquidity and Leverage Ratios over time)
    dbc.Row([
            dbc.Col(
                [
                    html.H6("Liquidity Ratios Over Time", className="font-weight-bold text-center mt-5", style={"font-size":"16px", "font-family": "Georgia, serif"}),
                    dcc.Graph(id='liquidity_ratios_chart', figure=get_four_charts(comp_branch_data, "CURRENT_ASSETS", "Current Assests", "CURRENT_LIABILITIES", "Current Liabilities", "WORKING_RATIO", "Wroking Capital Ratio", 
                    "QUICK_RATIO", "Quick Ratio", "Amount","Ratios"), className="shadow rounded", 
                    config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True})
                ], width=6), 

            dbc.Col(
                [
                    html.H6("Leverage Ratios Over Time", className="font-weight-bold text-center mt-5", style={"font-size":"16px", "font-family": "Georgia, serif"}),
                    dcc.Graph(id='leverage_ratios_chart', figure=get_four_charts(comp_branch_data, "ASSETS", "Assests", "LIABILITIES", "Liabilities", "DEBT_RATIO", "Debt Ratio", 
                    "DEBT_TO_EQUITY_RATIO", "D/E Ratio", "Amount","Ratios"), className="shadow rounded", 
                    config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True})
                ], width=6),
    ]),

    ## eigth row (final charts)
    dbc.Row(
        [
            dbc.Col(
                [
                    html.H6("Cash To Cash Cycle Over Time", className="font-weight-bold text-center mt-5", style={"font-size":"16px", "font-family": "Georgia, serif"}),
                    dcc.Graph(id='ctc_chart', figure=get_four_line_plots(comp_branch_data, "DSO", "DSO", "DIO", "DIO", "DPO", "DPO", "CASH_TO_CASH_CYCLE", "CTC Cycle", "Days"), className="shadow rounded",
                    config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True})
                
                ], width=6), 

            dbc.Col(
                [
                    html.H6("Profitability Ratios Over Time", className="font-weight-bold text-center mt-5", style={"font-size":"16px", "font-family": "Georgia, serif"}),
                    dcc.Graph(id='profitibility_chart', figure=get_two_line_plots(comp_branch_data, "RETURN_ON_ASSETS", "Return On Assets", "RETURN_ON_EQUITY", "Return On Equity", "Ratio"), className="shadow rounded",
                    config={
                    "scrollZoom":False,
                    "doubleclick":"reset", 
                    "showTips":True})
                
                ], width=6)

    ], className="mb-4")


], style={"background-color":"#f4f5ef"}, fluid=True)


## callbacks

@app.callback(
    [
        Output('net_sales_card','children'),
        Output('gross_margin_card','children'),
        Output('ar_card','children'),
        Output('ap_card','children'),
        Output('ctc_card','children'),
        Output('roa_card','children'),
        Output('roe_card','children'),
        Output('working_cap_card','children'),
        Output('working_cap_ratio_card','children'),
        Output('quick_ratio_card','children'),
        Output('debt_ratio_card','children'),
        Output('de_ratio_card','children'),
    ],
    [
        Input('company_drpdwn','value'),
        Input('ledger_drpdwn','value'),
        Input('year_drpdwn','value'),
        Input('month_drpdwn','value'),
    ],
)

def update_cards(company, ledger_sec, year, month):
    if month:
        net_sales = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].NET_SALES.sum())
        gross_margin = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].GROSS_MARGIN.sum())
        ar = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].AR.sum())
        ap = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].AP.sum())
        ctc = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].CASH_TO_CASH_CYCLE.sum())
        roa = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].RETURN_ON_ASSETS.sum())
        roe = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].RETURN_ON_EQUITY.sum())
        working_cap_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].CAPITAL.sum())
        cap_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].CAPITAL_RATIO.sum())
        quick_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].QUICK_RATIO.sum())
        debt_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].DEBT_RATIO.sum())
        de_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year) & (main_df['MONTH'] == month)].DEBT_TO_EQUITY_RATIO.sum())

        return(net_sales, gross_margin, ar, ap, ctc, roa, roe, working_cap_ratio, cap_ratio, quick_ratio, debt_ratio, de_ratio)
    
    elif year:
        net_sales = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].NET_SALES.sum())
        gross_margin = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].GROSS_MARGIN.sum())
        ar = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].AR.sum())
        ap = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].AP.sum())
        ctc = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].CASH_TO_CASH_CYCLE.sum())
        roa = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].RETURN_ON_ASSETS.sum())
        roe = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].RETURN_ON_EQUITY.sum())
        working_cap_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].CAPITAL.sum())
        cap_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].CAPITAL_RATIO.sum())
        quick_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].QUICK_RATIO.sum())
        debt_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].DEBT_RATIO.sum())
        de_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)].DEBT_TO_EQUITY_RATIO.sum())

        return(net_sales, gross_margin, ar, ap, ctc, roa, roe, working_cap_ratio, cap_ratio, quick_ratio, debt_ratio, de_ratio)

        
    else:
        net_sales = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].NET_SALES.sum())
        gross_margin = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].GROSS_MARGIN.sum())
        ar = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].AR.sum())
        ap = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].AP.sum())
        ctc = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].CASH_TO_CASH_CYCLE.sum())
        roa = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].RETURN_ON_ASSETS.sum())
        roe = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].RETURN_ON_EQUITY.sum())
        working_cap = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].CAPITAL.sum())
        cap_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].CAPITAL_RATIO.sum())
        quick_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].QUICK_RATIO.sum())
        debt_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].DEBT_RATIO.sum())
        de_ratio = float(main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)].DEBT_TO_EQUITY_RATIO.sum())
        
        return(net_sales, gross_margin, ar, ap, ctc, roa, roe, working_cap, cap_ratio, quick_ratio, debt_ratio, de_ratio)



## charts callback
@app.callback(
    [
        Output('gross_margin_ot','figure'),
        Output('operating_profit_ot','figure'),
        Output('liquidity_ratios_chart','figure'),
        Output('leverage_ratios_chart','figure'),
        Output('ctc_chart','figure'),
        Output('profitibility_chart','figure')],
    
    [
        Input('company_drpdwn','value'),
        Input('ledger_drpdwn','value'),
        Input('year_drpdwn','value'),
        Input('month_drpdwn','value'),
    ],
)

def update_charts(company, ledger_sec, year, month):
    if year:
        data = main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec) & (main_df['YEAR'] == year)]
        gross_margin_fig = get_dual_charts(data, "NET_SALES", "Net Sales", "COGS", "COGS", "GROSS_MARGIN_PERCENT", "Gross Margin (%)", "Amount", "Margin (%)")
        operating_profit_fig = get_dual_charts(data, "GROSS_MARGIN", "Gross Margin", "EXPENSES", "Expenses", "OPERATING_PROFIT_PERCENT", "Operating Profit (%)", "Amount", "Profit (%)")
        liquidity_ratio_fig = get_four_charts(data, "CURRENT_ASSETS", "Current Assests", "CURRENT_LIABILITIES", "Current Liabilities", "WORKING_RATIO", "Wroking Capital Ratio", 
                    "QUICK_RATIO", "Quick Ratio", "Amount","Ratios")
        leverage_ratios_fig = get_four_charts(data, "ASSETS", "Assests", "LIABILITIES", "Liabilities", "DEBT_RATIO", "Debt Ratio", 
                    "DEBT_TO_EQUITY_RATIO", "D/E Ratio", "Amount","Ratios")
        
        ctc_fig = get_four_line_plots(data, "DSO", "DSO", "DIO", "DIO", "DPO", "DPO", "CASH_TO_CASH_CYCLE", "CTC Cycle", "Days")
        profitibility_fig = get_two_line_plots(data, "RETURN_ON_ASSETS", "Return On Assets", "RETURN_ON_EQUITY", "Return On Equity", "Ratio")

        return gross_margin_fig, operating_profit_fig, liquidity_ratio_fig, leverage_ratios_fig, ctc_fig, profitibility_fig
    
    if ledger_sec:
        data = main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)]
        gross_margin_fig = get_dual_charts(data, "NET_SALES", "Net Sales", "COGS", "COGS", "GROSS_MARGIN_PERCENT", "Gross Margin (%)", "Amount", "Margin (%)")
        operating_profit_fig = get_dual_charts(data, "GROSS_MARGIN", "Gross Margin", "EXPENSES", "Expenses", "OPERATING_PROFIT_PERCENT", "Operating Profit (%)", "Amount", "Profit (%)")
        liquidity_ratio_fig = get_four_charts(data, "CURRENT_ASSETS", "Current Assests", "CURRENT_LIABILITIES", "Current Liabilities", "WORKING_RATIO", "Wroking Capital Ratio", 
                    "QUICK_RATIO", "Quick Ratio", "Amount","Ratios")
        leverage_ratios_fig = get_four_charts(data, "ASSETS", "Assests", "LIABILITIES", "Liabilities", "DEBT_RATIO", "Debt Ratio", 
                    "DEBT_TO_EQUITY_RATIO", "D/E Ratio", "Amount","Ratios")
        
        ctc_fig = get_four_line_plots(data, "DSO", "DSO", "DIO", "DIO", "DPO", "DPO", "CASH_TO_CASH_CYCLE", "CTC Cycle", "Days")
        profitibility_fig = get_two_line_plots(data, "RETURN_ON_ASSETS", "Return On Assets", "RETURN_ON_EQUITY", "Return On Equity", "Ratio")

        return gross_margin_fig, operating_profit_fig, liquidity_ratio_fig, leverage_ratios_fig, ctc_fig, profitibility_fig
    
    raise PreventUpdate


## charts callback
@app.callback([
    
        Output('ar_donut_chart', 'figure'),
        Output('ap_donut_chart','figure')],
    
    [
        Input('company_drpdwn','value'),
        Input('ledger_drpdwn','value'),
        Input('year_drpdwn','value'),
        Input('month_drpdwn','value')
    ],
)

def update_donut(company, ledger_sec, year, month):
    if month:
        data = main_df[(main_df['COMPANY_NAME'] == company) & (main_df['LEDGER_SECTION'] == ledger_sec)]

        ar_fig =  get_ar_donut(data, year, month)
        ap_fig =  get_ap_donut(data, year,month)

            
        return ar_fig, ap_fig
    
    raise PreventUpdate



if __name__ == "__main__":
    app.run_server(debug=False)
