import json
import time
from bs4 import BeautifulSoup
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


print("""
'   ██████╗ ██╗     ██╗  ██╗                                                  
'  ██╔═══██╗██║     ╚██╗██╔╝                                                  
'  ██║   ██║██║      ╚███╔╝                                                   
'  ██║   ██║██║      ██╔██╗                                                   
'  ╚██████╔╝███████╗██╔╝ ██╗                                                  
'   ╚═════╝ ╚══██████╗╝██╗═╝ ██╗              ███████╗ █████╗ ██████╗ ███████╗
'              ██╔══██╗╚██╗ ██╔╝              ██╔════╝██╔══██╗██╔══██╗██╔════╝
'              ██████╔╝ ╚████╔╝     █████╗    █████╗  ███████║██████╔╝█████╗  
'              ██╔══██╗  ╚██╔╝      ╚════╝    ██╔══╝  ██╔══██║██╔══██╗██╔══╝  
'              ██████╔╝   ██║                 ██║     ██║  ██║██║  ██║███████╗
'              ╚═════╝    ╚═╝                 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
'                                                                             
""")
from munch import DefaultMunch

# Fetch service account key JSON file contents
cred = credentials.Certificate("serviceAccountKey.json")

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://olx-web-scraper-default-rtdb.firebaseio.com/"
})

# Save data
ref = db.reference()
products_ref = ref.child('products')


class Product:
    def __init__(self, product_name, product_time, product_price, ):
        self._product_name = product_name
        self._product_time = product_time
        self._product_price = product_price

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    # Static variable
    numberOfCorresponding = 0
    latestObj = []

    # Print the products that match the time
    def getLatestInConsole(self, time_elapsed):
        time = ''
        if '' in self._product_time:
            for char in self._product_time[-6:]:
                if char.isdigit():
                    time += char

        if len(time) > 0:
            if int(time) <= time_elapsed:
                Product.numberOfCorresponding += 1
                Product.latestObj.append(self)
                time += ' min'
                return f"Naziv proizvoda: {self._product_name}\n" \
                       f"Vrijeme objave: {self._product_time}\n" \
                       f"Cijena: {self._product_price}\n"
        return ''

    # Write products that match the time to a file
    def getLatestInFile(self, products_file, time_elapsed):
        stringToWrite = self.getLatestInConsole(time_elapsed + "n")
        if stringToWrite != '':
            products_file.writelines()


listOfValidProducts = []
listOfNames = []


# Scrape products from weblink
def scrapeProductsWithLink(website_link, time_elapsed_after_posting, choice):
    website_link = 'https://www.olx.ba/pretraga?kategorija=31&id=3&stanje=0&vrstapregleda=tabela&sort_order=desc&sort_po=datum'
    html_text = requests.get(website_link, headers={'User-Agent': 'Mozilla/5.0'}).text

    soup = BeautifulSoup(html_text, 'lxml')

    products_file = open(f'products.txt', 'w')

    # Nadjem svaki proizvod
    scrape_result = soup.find_all('div', id=lambda x: x and x.startswith('art_'))

    # Za svaki proizvod nadjem cijenu
    for tag in scrape_result:
        product_name = tag.find('p').text
        product_time = tag.find("div", class_='datum').find("div").text
        product_price = tag.find("div", class_='datum').find("span").text

        product = Product(product_name, product_time, product_price)

        if choice == 1 or choice == 2:
            stringToPrint = product.getLatestInConsole(time_elapsed_after_posting)
            if stringToPrint != '':
                if choice == 2:
                    print(stringToPrint)
                listOfNames.append(product._product_name.replace(".", " ").replace("/", " "))
                listOfValidProducts.append(product.__dict__)
        else:
            product.getLatestInFile(products_file, time_elapsed_after_posting)

    products_file.close()

    print(f"Found {Product.numberOfCorresponding}!")


choice = ''
max_time = ''
should_restart = ''
wait_time = ''


def getInput():
    global choice
    global max_time
    global should_restart
    global wait_time
    # Get the input from the user and check if its a desired value
    while True:
        choice = input("Do you want to print or write to file (1 no | 2 print | 2 wtf): ")

        if not choice.isnumeric():
            print(print("Please enter a number!\n"))
            continue
        if int(choice) != 1 and int(choice) != 2 and int(choice) != 3:
            print("Please choose 1 or 2\n")
            continue

        max_time = input("Enter the max time after posting you want to see (<60min): ")

        if not max_time.isnumeric():
            print(print("Please enter a number!\n"))
            continue
        if int(max_time) > 60:
            print("Max time is 60 min\n")
            continue

        should_restart = input("Should I run periodically (1 yes | 2 no) ")
        if not should_restart.isnumeric():
            print(print("Please enter a number!\n"))
            continue
        if int(should_restart) != 1 and int(should_restart) != 2:
            print("Please choose 1 or 2\n")
            continue

        if int(should_restart) == 1:
            wait_time = input("How long should I wait (minutes) to run again: ")
        if not max_time.isnumeric():
            print(print("Please enter a number!\n"))
            continue

        print()
        break


def runScraper():
    while True:
        scrapeProductsWithLink('fixed_value', int(max_time), int(choice))

        dictOfProducts = dict(zip(listOfNames, listOfValidProducts))
        products_ref.set(dictOfProducts)

        if int(should_restart) == 1:
            print(f"Running again in {wait_time} min")
            Product.numberOfCorresponding = 0
            time.sleep(float(wait_time) * 60)
        else:
            break


# Add for production
if __name__ == '__main__':
    getInput()
    runScraper()

# for productKey in test:
#     print(DefaultMunch.fromDict(test[productKey])._product_name)
