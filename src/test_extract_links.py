import requests
from bs4 import BeautifulSoup

URL = "https://www.urjc.es/estudios/grado/640-ingenieria-software#informe-de-resultados"

def main():

    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "lxml")

    links = []

    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".pdf"):
            links.append(a["href"])

    print("PDFs encontrados:", len(links))

    for link in links[:10]:
        print(link)


if __name__ == "__main__":
    main()