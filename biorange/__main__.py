import typer

app = typer.Typer()

@app.command()
def main():
    print("helloworld")

if __name__ == "__main__":
    app()
