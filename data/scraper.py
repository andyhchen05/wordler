import requests
from bs4 import BeautifulSoup

url = "https://wordletools.azurewebsites.net/weightedbottles"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

with open("../data/answers.txt", "w") as answer_file:
    with open("../data/weights.txt", "w") as weight_file:

        for row in soup.find_all("tr"):

            cells = row.find_all("td")

            if len(cells) >= 2:

                word = cells[0].get_text(strip=True).lower()
                weight = cells[1].get_text(strip=True)

                if len(word) == 5 and word.isalpha():

                    answer_file.write(word + "\n")
                    weight_file.write(word + " " + weight + "\n")

print("Done.")