import tika
from tika import parser
import re
from bs4 import BeautifulSoup
import json

tika.initVM()

class Paper:
    def __init__(self, tei_doc):
        self.tei = tei_doc
        with open(tei_doc, 'r') as tei:
            self.soup = BeautifulSoup(tei, features="xml")
        self.title = self.soup.title.getText()
        self.doi = self.doi_retrieve()
        # self.url = self.tika_check()

        self.paragraphs = self.paragrapher()
        self.citations = self.citation_finder()
        self.references = self.reference_matcher()
        self.footnotes = self.footnote_finder()

    def doi_retrieve(self):
        # retrieves pdf DOI from soup if available
        idno_elem = self.soup.find('idno', type='DOI')
        if not idno_elem:
            self.doi = ''
        else:
            self.doi = idno_elem.getText()

    def is_string_an_url(self, url_string: str) -> bool:
        result = validators.url(url_string)

        return result if result else False

    def extractURL(self, string):
        # Creating an empty list
        url_list = []
        true_url = []

        # Regular Expression to extract URL from the string
        regex = r'\b((?:https?|ftp|file):\/\/[-a-zA-Z0-9+&@#\/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#\/%=~_|])(?:\n)?'
        
        # Compile the Regular Expression
        p = re.compile(regex, re.IGNORECASE)
        
        # Find the match between string and the regular expression
        m = p.finditer(string)
        
        # Find the next subsequence of the input subsequence that find the pattern
        for match in m:
            # Find the substring from the first index of match result to the last index of match result and add in the list
            url_list.append(match.group())
        
        
        # Print all the URLs stored
        for url in url_list:

            #check if found URL is a valid URL
            if self.is_string_an_url(url):
                true_url.append(url)

            else:
                print('wrong URL:', url)

        return true_url

    def paragrapher(self):
        # function that retrieves all a pdf's paragraphs
        return [para for para in self.soup.find_all("p")]

    def reference_finder(self):
        # function that returns a list of lists of references present in a pdf's paragraphs
        reference_list = []

        for paragraph in [para for para in self.paragraphs]:
            refs = paragraph.find_all('ref')
            reference_list.append(refs)
        
        return reference_list

    def citation_finder(self):
        # function that returns a list of citations present in a pdf citations
        return self.soup.select('biblStruct')

    def reference_matcher(self):
        # this function matches each paragraph to any references that might point to it, producing a list of reference soups for each paragaraph.
        reference_per_paragraph = []

        for paragraph in self.paragraphs:
            correct_list = []
            failed_list = []

            # list of bibliography references present in paragraph
            refs =  paragraph.find_all('ref', type="bibr")

            # here we find the id of the reference present in the paragraph in order to link it to the citations            
            for ref in refs:
                try:
                    target = ref['target'][1:]
                    correct_list.append(target)

                except:
                    failed_list.append(ref)
                    continue
            
            # if this paragraph contains any references that have an id:
            if correct_list:
                for i, id_ in enumerate(correct_list):

                    for citation in self.citations:
                        
                        try:
                            if citation['xml:id'] == id_:
                                correct_list[i] = citation

                        except:
                            continue

            else:
                reference_per_paragraph.append([])
                ### PUT SOME CODE HERE THAT CAN STRING MATCH REFERENCES IN THE FUTURE USING FAILED_LIST ###
                continue
            
            reference_per_paragraph.append(correct_list)
        
        return reference_per_paragraph

    def footnote_finder(self):
        # this function returns a list of the length of the amount of paragraphs in the paper and the corresponding footnotes associated to that paragraph.
        footnotes = []

        # find all footnotes that grobid found.
        foot_elem = self.soup.find_all('note', place='foot')

        for paragraph in self.paragraphs:
            citation_list = []

            # find the references in the text that link to footnotes
            ref = paragraph.find_all('ref', type="foot")

            # if there are any of those footnotes, we try and match them with the footnotes we found in the text.
            if ref:
                for footnote in foot_elem:
                    
                    for r in ref:
                        if footnote['xml:id'] == r['target'][1:]:
                            citation_list.append(footnote)
                footnotes.append(citation_list)
            else:        
                footnotes.append(ref)

        return footnotes

    def in_text_URL(self):
        # function that finds in-text URL's per paragraph
        all_url = []

        for paragraph in self.paragraphs:
            paragraph = paragraph.getText()
            urls_found = self.extractURL(paragraph)
            all_url.append(urls_found)

        return all_url

    def tika_check(self):
        # use Tika to find URL's hidden in footnotes that grobid might miss
        parsed_pdf = parser.from_file(self.tei)
        pdf_text = parsed_pdf
        # print(parsed_pdf['content'])

        # extract URLs using regex
        list_URLS = self.extractURL(pdf_text)
        
        return list_URLS

    def store_info_as_json(self, output_file):
        data = []
        for i, paragraph in enumerate(self.paragraphs):
            paragraph_info = {
                "id": i + 1,
                "text": paragraph.get_text(),
                "references": self.reference_matcher()[i],
                "footnotes": self.footnote_finder()[i],
                "urls": self.in_text_URL()[i]
            }
            data.append(paragraph_info)

        with open(output_file, "w") as f:
            json.dump(data, f, indent=4, default = str)
