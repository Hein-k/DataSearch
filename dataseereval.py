from find_links import Paper
from bs4 import BeautifulSoup

if __name__ == "__main__":

    paper = Paper('output.xml')

    # print(paper.citations)
    for paragraph in paper.paragraphs:

        if "The dataset is available" in paragraph.getText():
            print(paragraph)
        # print(paragraph.getText())

    with open('output.xml', 'r') as tei:
        soup = BeautifulSoup(tei, features="xml")

    # for tag in soup.findAll(True):
    #     print(tag.name)

    # print(set([tag.name for tag in soup.findAll(True)]))

    # print(soup.find_all('dataInstance'))

# print(len(paper.references))
# print(len(paper.paragraphs))