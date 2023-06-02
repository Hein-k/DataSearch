import tika
from tika import parser
import validators
import re
import grobid_tei_xml
from bs4 import BeautifulSoup
import json
from fuzzywuzzy import fuzz

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
        pdf_text = parsed_pdf['content']
        # print(pdf_text)

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

class contextExtractor:
    # takes as input a paper object and outputs a classification of the URLs present. 

    def __init__(self, tei_doc):
        self.paper = Paper(tei_doc)
        self.url_dict = {}
        self.candidate_dataset_names = ['CAPRI', 'FADN', 'FSS', 'Agricultural Outlook']

    def dataset(self):
        # iterates over the candidate datasets to find a suitable URL

        for dataset in self.candidate_dataset_names:
            mentioning_paragraphs = self.find_mentions(dataset)

    def reference_iterator(self):
        for reference in self.paper.citations:
            # print(reference.find('title'))
            if reference.find('title').getText() == 'Agricultural Outlook':
                print(reference.find('title').parent)
            # print()

    def find_mentions(self, dataset):
        # finds all mentions of a given dataset

        # print(len(self.paper.references))
        for (paragraph, reference_list, footnote_list) in zip(self.paper.paragraphs, self.paper.references, self.paper.footnote_finder()):
            paragraph_text = paragraph.getText()
            
            # if there is a reference in the current paragraph:
            if reference_list:
                self.reference_analysis(dataset, paragraph, reference_list)

            self.footnote_analysis(dataset, paragraph, footnote_list)

            # if dataset in paragraph_text:
            #     print('DATASET FOUND IN PARAGRAPH')
            #     print(paragraph_text)
            #     print()

            # if dataset in citation:
            #     print('DATASET FOUND IN CITATION')
            #     print(citation)
            #     print()
        print(self.url_dict)


    def reference_analysis(self, dataset, paragraph, reference_list):
        # This function takes care of the analysis of the citation, it scans the citation for any dataset mention and then uses H1, H2 and H3 to determine if there is a connection

        for reference in reference_list:
            try:
                # this code block finds information about the reference only if it contains a link.
                reference_id = reference.find('ptr').parent.parent['xml:id']
                context = reference.find('ptr').parent
                url = reference.find('ptr')['target']
                title = context.find('title').getText()
                author_name = reference.find('persName').getText()
                
            except:
                continue
            
            # this finds how the reference is put in the paragraph for each reference.
            reference_in_text = paragraph.find_all('ref', target = '#' + reference_id)[0].getText()

            # H1
            if self.h1(paragraph, dataset, reference_in_text, threshold = 40):
                self.url_dict[dataset] = url
                # print('found in refs:',dataset, url)

            # H2
            if self.h2(dataset, title):
                self.url_dict[dataset] = url              

            # H3

    def footnote_analysis(self, dataset, paragraph, footnote_list):
        # loops over the paragraphs and finds corresponding footnotes and applies H1, H2 and H3 to them.

        # loop over the potentially multiple footnotes of this paragraph
        for footnote in footnote_list:
            try:
                footnote_n = footnote['n']
                footnote_id = footnote['xml:id']
                footnote_text = footnote.getText()
                footnote_links_list = self.paper.extractURL(footnote_text)
                
                # check if there's more than one link in footnote
                if len(footnote_links_list) != 1:
                    raise Exception("More than one link found in footnotes")

            except:
                continue

            # H1 
            # this finds how the reference is put in the paragraph for each reference.
            reference_in_text = paragraph.find_all('ref', target = '#' + footnote_id)[0].getText()

            if self.h1(paragraph, dataset, reference_in_text, threshold = 20):
                self.url_dict[dataset] = footnote_links_list[0]

            # H2
            if self.h2(dataset, footnote_text):
                self.url_dict[dataset] = footnote_links_list[0]
            


    def character_distance(self, string, part1, part2):
        index1 = string.index(part1)
        index2 = string.index(part2)
        distance = abs(index2 - index1) - len(part1)

        return distance

    def h1(self, paragraph, dataset_name, reference_with_link, threshold = 80):
        # Closeness candidate dataset name and URL

        try:
            distance = self.character_distance(paragraph.getText(), dataset_name, reference_with_link)
            
            if distance < threshold:
                return True
            else:
                return False
        except:
            pass

    def h2(self, dataset_name, string, threshold=80):
        
        # generate possible acronyms of the length of the dataset that can be formed by the string and that have to be checked 
        # print(string, len([*dataset_name]))
        possible_acronyms = self.get_acron(string, len([*dataset_name]))

        # first loop loops over the dataset_name that was given but also changes it to an acronym to see if that has effect
        for potential in [dataset_name, ''.join([word[0] for word in dataset_name.split()])]:

            # loop over the words in the string and the possible acronyms that it can generate
            for string_word in string.split() + possible_acronyms:
                # print('string:',string_word)

                # Check if the word, its acronym, or expanded form is closely related to the string word
                similarity_score = fuzz.ratio(potential.lower(), string_word.lower())

                if similarity_score >= threshold:
                    # print('potential',potential)
                    # print('string_word:',string_word)
                    return True
            
        return False


    def h3(self):
        # URL metadata check
        pass

    def get_acron(self, string, N):
        # takes a string and provides with possible acronyms in the text
        words = string.split()
        acronym = ''.join(word[0].upper() for word in words)

        substrings = []
        for i in range(len(acronym) - N + 1):
            substring = acronym[i:i+N]
            if len(set(substring)) == N:
                substrings.append(substring)

        return substrings


if __name__ == "__main__":
    tei_doc = '1-s2.0-S0308521X18307728-main.pdf.tei.xml'
    text_object = Paper(tei_doc)
    text_object.tika_check()

    context_obj = contextExtractor(tei_doc)

    context_obj.reference_iterator()

    # print(text_object.store_info_as_json('output.json'))

    
            
        
