import reflex as rx

from .rag.main import rag_ai_app


# !update UI for easier demoing
def index():
    return rag_ai_app()


app = rx.App()
app.add_page(index)
