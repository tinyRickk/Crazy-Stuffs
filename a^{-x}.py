##found at: https://www.youtube.com/watch?v=0WqpLYrWu7g, https://www.dropbox.com/scl/fi/7nu8izoyqwccfx9p7a4i3/trumpet_visualiser.py?rlkey=k2prmqocuv1ry8l33rjxu580w&e=1&dl=0

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask_caching import Cache


external_stylesheets = [dbc.themes.SOLAR]
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})


initial_ks = list(range(-5, 6))
colors = ['hsl({}, 50%, 60%)'.format(int(360 * i / len(initial_ks))) for i in range(len(initial_ks))]


x_step_marks = {0.001: '1/1000', 0.01: '1/100', 0.1: '1/10', 1.0: '1'}


control_card = dbc.Card(
    dbc.CardBody([
        html.H5("Controls", className='card-title text-muted'),
        dcc.Store(id='all-ks', data=initial_ks),


        dbc.Label("Base (enter real or negative number):", className='mt-2'),
        dbc.Input(id='base-input', type='number', value=-2, step=0.1),


        html.Hr(),
        dbc.Label("Select Branches (k):", className='mt-2'),
        dcc.Checklist(
            id='branches',
            options=[{'label': f'k = {k}', 'value': k} for k in initial_ks],
            value=initial_ks,
            inline=True,
            inputStyle={'margin': '0 5px 0 15px'}
        ),
        dbc.Row([
            dbc.Col(dcc.Input(id='custom-k', type='number', placeholder='Add k...', size='small'), width=6),
            dbc.Col(dbc.Button('Add', id='add-k', color='secondary', size='sm'), width=6)
        ], className='mt-2'),


        html.Hr(),
        dbc.Label("Connect Dots:"),
        dbc.Checklist(
            id='line-mode',
            options=[{'label': 'Yes', 'value': 'lines'}],
            value=['lines'],
            switch=True,
            inline=True,
        ),
        html.Br(),


        dbc.Label("Dot Size:"),
        dcc.Slider(
            id='dot-size',
            min=1, max=10, step=1, value=4,
            marks={i: str(i) for i in range(1, 11)},
            tooltip={'placement': 'bottom', 'always_visible': False}
        ),
        html.Br(),


        dbc.Label("x Spacing:"),
        dcc.Slider(
            id='x-step',
            min=0.001, max=1.0, step=0.001, value=0.004,
            marks=x_step_marks,
            tooltip={'placement': 'bottom', 'always_visible': True}
        ),
        html.Div(id='x-step-display', className='text-end text-muted small mt-1'),
    ]),
    className='mb-4',
    style={'backgroundColor': '#f8f9fa', 'border': 'none', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}
)


app.layout = html.Div([
    dbc.Container([
        dbc.Row(dbc.Col(html.H1(id='title', className='text-center my-4 text-secondary'))),
        dbc.Row([
            dbc.Col(control_card, width=3),
            dbc.Col(dcc.Loading(dcc.Graph(id='complex-plot', style={"height": "75vh"})), width=9)
        ])
    ], fluid=True),
    html.Footer(style={'height': '100px', 'backgroundColor': '#f8f9fa'})
], style={'backgroundColor': '#e9ecef', 'paddingBottom': '0'})


@app.callback(
    Output('title', 'children'),
    Input('base-input', 'value')
)
def update_title(base):
    return f"{base}^x Explorer"


@cache.memoize(timeout=60)
def compute_traces(base, all_ks, selected_ks, line_on, dot_size, x_step):
    x = np.arange(-5, 5, x_step)
    traces = []
    base_complex = complex(base)
    ln_base = np.log(np.abs(base_complex))
    arg_base = np.angle(base_complex)
    for idx, k in enumerate(all_ks):
        if k not in selected_ks:
            continue
        exp_term = x * (ln_base + 1j*(arg_base + 2*np.pi*k))
        z = np.exp(exp_term)
        real, imag = np.real(z), np.imag(z)
        traces.append(go.Scatter3d(
            x=real, y=imag, z=x,
            mode='lines+markers' if line_on else 'markers',
            name=f'k = {k}',
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=dot_size),
            hoverinfo='name'
        ))
    return traces


@app.callback(
    Output('all-ks', 'data'),
    Output('branches', 'options'),
    Output('branches', 'value'),
    Input('add-k', 'n_clicks'),
    State('custom-k', 'value'),
    State('all-ks', 'data'),
    State('branches', 'value')
)
def add_custom_k(n, new_k, all_ks, selected):
    if n and new_k is not None:
        if new_k not in all_ks:
            all_ks = sorted(all_ks + [new_k])
            selected = selected + [new_k]
    options = [{'label': f'k = {k}', 'value': k} for k in all_ks]
    return all_ks, options, selected


@app.callback(
    Output('complex-plot', 'figure'),
    Input('base-input', 'value'),
    Input('all-ks', 'data'),
    Input('branches', 'value'),
    Input('line-mode', 'value'),
    Input('dot-size', 'value'),
    Input('x-step', 'value')
)
def update_plot(base, all_ks, selected_ks, line_mode, dot_size, x_step):
    line_on = 'lines' in line_mode
    traces = compute_traces(base, tuple(all_ks), tuple(selected_ks), line_on, dot_size, x_step)
    fig = go.Figure(data=traces)
    fig.update_layout(
        template='plotly_white',
        scene=dict(
            xaxis_title='Real', yaxis_title='Imag', zaxis_title='x'
        ),
        showlegend=True,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    return fig


@app.callback(
    Output('x-step-display', 'children'),
    Input('x-step', 'value')
)
def display_x_step(val):
    denom = int(round(1/val)) if val else 0
    return f"Spacing: 1/{denom} (~{val:.4f})"


if __name__ == '__main__':
    app.run(debug=False)
