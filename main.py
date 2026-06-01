from pathlib import Path
import io
import json
import fitz
import dash
from dash import html, dcc, Input, Output, State, ALL, ctx

PDF_DIR = Path(__file__).parent / "data"
TEXT_FILE = Path(__file__).parent / "texts.json"


def load_texts():
    if TEXT_FILE.exists():
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_texts(data):
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
CATEGORIES = ["安全", "生産", "人財", "品質", "原価"]
ROWS = ["課方針", "目標", "メインKPI", "サブKPI"]

app = dash.Dash(__name__)

TEXT_INPUT_ROWS = ["課方針", "目標"]

MODAL_BASE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "width": "100vw",
    "height": "100vh",
    "backgroundColor": "rgba(0,0,0,0.7)",
    "zIndex": 1000,
    "justifyContent": "flex-start",
    "alignItems": "flex-start",
}


def cell_content(category, row, saved=None):
    if row in TEXT_INPUT_ROWS:
        value = (saved or {}).get(f"{category}_{row}", "")
        return html.Div([
            dcc.Textarea(
                id={"type": "text-input", "cat": category, "row": row},
                value=value,
                style={
                    "width": "100%",
                    "height": "80px",
                    "resize": "vertical",
                    "border": "1px solid #ccc",
                    "padding": "4px",
                    "fontSize": "14px",
                    "boxSizing": "border-box",
                }
            ),
            html.Div(
                html.Button(
                    "拡大表示",
                    id={"type": "text-view-btn", "cat": category, "row": row},
                    n_clicks=0,
                    style={
                        "marginTop": "4px",
                        "padding": "2px 10px",
                        "fontSize": "12px",
                        "cursor": "pointer",
                        "backgroundColor": "#4472C4",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "3px",
                    }
                )
            )
        ])
    folder = PDF_DIR / category / row
    if not folder.is_dir():
        return html.Span("-", style={"color": "#ccc"})
    files = [f.name for f in folder.iterdir() if f.suffix.lower() == ".pdf"]
    if not files:
        return html.Span("-", style={"color": "#ccc"})
    return html.Div([
        html.Div([
            html.Img(
                src=f"/pdf-preview/{category}/{row}/{f}",
                style={"width": "100%", "height": "auto", "display": "block", "border": "1px solid #ddd"}
            ),
            html.Div([
                html.Span(f, style={"fontSize": "11px", "color": "#666", "verticalAlign": "middle"}),
                html.Button(
                    "拡大表示",
                    id={"type": "view-btn", "src": f"/data/{category}/{row}/{f}"},
                    n_clicks=0,
                    style={
                        "marginLeft": "8px",
                        "padding": "2px 10px",
                        "fontSize": "12px",
                        "cursor": "pointer",
                        "backgroundColor": "#4472C4",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "3px",
                        "verticalAlign": "middle",
                    }
                ),
            ], style={"marginTop": "4px", "marginBottom": "8px"})
        ])
        for f in sorted(files)
    ])


HEADER_STYLE = {
    "textAlign": "center",
    "padding": "10px 16px",
    "backgroundColor": "#4472C4",
    "color": "white",
    "border": "1px solid #ccc",
    "fontWeight": "bold",
    "width": "18%",
}

HEADER_LABEL_STYLE = {
    **{
        "textAlign": "center",
        "padding": "10px 16px",
        "backgroundColor": "#4472C4",
        "color": "white",
        "border": "1px solid #ccc",
        "fontWeight": "bold",
    },
    "width": "6%",
}

ROW_LABEL_STYLE = {
    "fontWeight": "bold",
    "padding": "16px 16px",
    "backgroundColor": "#D9E1F2",
    "border": "1px solid #ccc",
    "whiteSpace": "nowrap",
    "width": "6%",
    "textAlign": "center",
}

CELL_STYLE = {
    "padding": "8px 12px",
    "border": "1px solid #ccc",
    "verticalAlign": "top",
    "width": "18%",
}

CELL_STYLE_PDF = {
    "padding": "16px 12px",
    "border": "1px solid #ccc",
    "verticalAlign": "top",
    "width": "18%",
}


def pdf_modal():
    return html.Div(
        id="pdf-modal-overlay",
        style={**MODAL_BASE, "display": "none"},
        children=[
            html.Div([
                html.Div([
                    html.Button(
                        "✕ 閉じる",
                        id="close-modal-btn",
                        n_clicks=0,
                        style={
                            "float": "right",
                            "cursor": "pointer",
                            "padding": "4px 14px",
                            "backgroundColor": "#e74c3c",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "3px",
                            "fontSize": "14px",
                        }
                    ),
                    html.Div(style={"clear": "both"}),
                ], style={"marginBottom": "8px"}),
                html.Iframe(
                    id="modal-pdf-iframe",
                    src="",
                    style={"width": "100%", "height": "90vh", "border": "none", "display": "block"}
                )
            ], style={
                "backgroundColor": "white",
                "padding": "16px",
                "borderRadius": "8px",
                "width": "95vw",
            })
        ]
    )


def text_modal():
    return html.Div(
        id="text-modal-overlay",
        style={**MODAL_BASE, "display": "none"},
        children=[
            html.Div([
                html.Div([
                    html.Span(id="text-modal-title", style={"fontWeight": "bold", "fontSize": "16px"}),
                    html.Button(
                        "✕ 閉じる",
                        id="close-text-modal-btn",
                        n_clicks=0,
                        style={
                            "cursor": "pointer",
                            "padding": "4px 14px",
                            "backgroundColor": "#e74c3c",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "3px",
                            "fontSize": "14px",
                        }
                    ),
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"}),
                dcc.Textarea(
                    id="modal-textarea",
                    value="",
                    style={
                        "width": "100%",
                        "height": "75vh",
                        "fontSize": "16px",
                        "padding": "8px",
                        "border": "1px solid #ccc",
                        "resize": "none",
                        "boxSizing": "border-box",
                    }
                )
            ], style={
                "backgroundColor": "white",
                "padding": "16px",
                "borderRadius": "8px",
                "width": "80vw",
            })
        ]
    )


def serve_layout():
    saved = load_texts()
    return html.Div([
        pdf_modal(),
        text_modal(),
        dcc.Store(id="text-modal-store", data={"cat": "", "row": ""}),
        dcc.Store(id="menu-open", data=False),
        html.Div(
            id="sidebar",
            children=[
                html.Div([
                    html.P("班選択", style={"fontWeight": "bold", "margin": "0", "color": "#2F3F60"}),
                    html.Button("✕", id="sidebar-close-btn", n_clicks=0, style={
                        "background": "none", "border": "none", "cursor": "pointer",
                        "fontSize": "18px", "color": "#2F3F60", "padding": "0",
                    }),
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"}),
                html.Button("A班", id="btn-a-han", n_clicks=0, style={
                    "display": "block", "width": "100%", "marginBottom": "8px",
                    "padding": "8px", "backgroundColor": "#4472C4", "color": "white",
                    "border": "none", "borderRadius": "4px", "cursor": "pointer", "fontSize": "16px",
                }),
                html.Button("B班", id="btn-b-han", n_clicks=0, style={
                    "display": "block", "width": "100%",
                    "padding": "8px", "backgroundColor": "#4472C4", "color": "white",
                    "border": "none", "borderRadius": "4px", "cursor": "pointer", "fontSize": "16px",
                }),
            ],
            style={
                "position": "fixed", "top": "0", "left": "-200px",
                "width": "180px", "height": "100vh",
                "backgroundColor": "#f0f4ff", "padding": "20px 12px",
                "boxShadow": "2px 0 8px rgba(0,0,0,0.2)",
                "zIndex": 2000, "transition": "left 0.3s ease",
            }
        ),
        html.Div([
            html.Div(
                html.Button("☰", id="menu-btn", n_clicks=0, style={
                    "fontSize": "24px",
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "color": "#2F3F60",
                    "padding": "0 12px",
                }),
                style={"flex": "1", "display": "flex", "alignItems": "center"}
            ),
            html.H1("品質管理部五大任務デジタルボード", style={
                "textAlign": "center",
                "padding": "0",
                "margin": "0",
                "fontSize": "30px",
                "lineHeight": "1",
                "color": "#2F3F60",
                "flex": "1",
            }),
            html.Div([
                html.Div(id="datetime-display", style={
                    "fontSize": "20px",
                    "color": "#2F3F60",
                    "textAlign": "right",
                    "lineHeight": "1.5",
                }),
                dcc.Interval(id="clock-interval", interval=1000, n_intervals=0),
            ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end", "paddingRight": "12px"}),
        ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
        html.Div(
            html.Span(id="save-status", style={"fontSize": "12px", "color": "#217346"}),
            style={"padding": "4px 12px", "minHeight": "24px"}
        ),
        html.Table([
            html.Thead(html.Tr(
                [html.Th("KPI", style=HEADER_LABEL_STYLE)] +
                [html.Th(cat, style=HEADER_STYLE) for cat in CATEGORIES]
            )),
            html.Tbody([
                html.Tr([
                    html.Td(row, style={**ROW_LABEL_STYLE, "padding": "8px 16px"} if row in TEXT_INPUT_ROWS else ROW_LABEL_STYLE),
                    *[html.Td(cell_content(cat, row, saved), style=CELL_STYLE_PDF if row not in TEXT_INPUT_ROWS else CELL_STYLE) for cat in CATEGORIES]
                ])
                for row in ROWS
            ])
        ], style={"borderCollapse": "collapse", "width": "100%", "tableLayout": "fixed"}),
    ], style={"padding": "0"})


app.layout = serve_layout


@app.callback(
    Output("sidebar", "style"),
    Input("menu-btn", "n_clicks"),
    Input("sidebar-close-btn", "n_clicks"),
    State("sidebar", "style"),
    prevent_initial_call=True,
)
def toggle_sidebar(_menu, _close, current_style):
    style = dict(current_style)
    if ctx.triggered_id == "sidebar-close-btn":
        style["left"] = "-200px"
    else:
        style["left"] = "-200px" if current_style.get("left") == "0px" else "0px"
    return style


@app.callback(
    Output("datetime-display", "children"),
    Input("clock-interval", "n_intervals"),
)
def update_clock(_):
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%Y/%m/%d %H:%M:%S")


@app.callback(
    Output("save-status", "children"),
    Input({"type": "text-input", "cat": ALL, "row": ALL}, "n_blur"),
    State({"type": "text-input", "cat": ALL, "row": ALL}, "value"),
    State({"type": "text-input", "cat": ALL, "row": ALL}, "id"),
    prevent_initial_call=True,
)
def auto_save(_n_blurs, values, ids):
    data = {f"{d['cat']}_{d['row']}": v or "" for d, v in zip(ids, values)}
    save_texts(data)
    return "自動保存済み ✓"


@app.callback(
    Output("text-modal-overlay", "style"),
    Output("modal-textarea", "value"),
    Output("text-modal-store", "data"),
    Output("text-modal-title", "children"),
    Input({"type": "text-view-btn", "cat": ALL, "row": ALL}, "n_clicks"),
    Input("close-text-modal-btn", "n_clicks"),
    State({"type": "text-input", "cat": ALL, "row": ALL}, "value"),
    State({"type": "text-input", "cat": ALL, "row": ALL}, "id"),
    State("text-modal-store", "data"),
    State("modal-textarea", "value"),
    prevent_initial_call=True,
)
def toggle_text_modal(_view_clicks, _close_click, text_values, text_ids, store_data, modal_value):
    triggered = ctx.triggered_id

    if triggered == "close-text-modal-btn":
        cat, row = store_data.get("cat"), store_data.get("row")
        if cat and row:
            data = load_texts()
            data[f"{cat}_{row}"] = modal_value or ""
            save_texts(data)
        return {**MODAL_BASE, "display": "none"}, "", {"cat": "", "row": ""}, ""

    if isinstance(triggered, dict) and triggered.get("type") == "text-view-btn":
        cat, row = triggered["cat"], triggered["row"]
        value = next((v or "" for d, v in zip(text_ids, text_values) if d["cat"] == cat and d["row"] == row), "")
        return {**MODAL_BASE, "display": "flex"}, value, {"cat": cat, "row": row}, f"{cat} - {row}"

    raise dash.exceptions.PreventUpdate


@app.callback(
    Output("pdf-modal-overlay", "style"),
    Output("modal-pdf-iframe", "src"),
    Input({"type": "view-btn", "src": ALL}, "n_clicks"),
    Input("close-modal-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(_view_clicks, _close_click):
    triggered = ctx.triggered_id

    if triggered == "close-modal-btn":
        return {**MODAL_BASE, "display": "none"}, ""

    if isinstance(triggered, dict) and triggered.get("type") == "view-btn":
        return {**MODAL_BASE, "display": "flex"}, triggered["src"]

    raise dash.exceptions.PreventUpdate


@app.server.route("/pdf-preview/<category>/<row>/<filename>")
def serve_pdf_preview(category, row, filename):
    from flask import send_file
    pdf_path = PDF_DIR / category / row / filename
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False)
    img_bytes = pix.tobytes("png")
    doc.close()
    return send_file(io.BytesIO(img_bytes), mimetype="image/png")


@app.server.route("/data/<category>/<row>/<filename>")
def serve_pdf(category, row, filename):
    from flask import send_from_directory
    folder = PDF_DIR / category / row
    return send_from_directory(folder, filename)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
