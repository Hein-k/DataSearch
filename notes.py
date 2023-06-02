def text_analysis(soup):


    
    # text_citations = soup.reference.getText()

    # print(text_citations)
    # # URL_list = extractURL(text_body)
    # print(URL_list)
    pass

### IN: (multiple) PDF ###
def URL_find(tei_doc):
    text_analysis(tei_doc)
    # Find URL
    # URLs = extractURL(data)

    # Establish location URL (footnote, citation, reference)

    # Heuristic to determine if it is a dataset?

    # Return surrounding paragraph

    # return
### OUT: URL, location, dataset? (Y/n), surrounding paragraph

### Establish location of URL (footnote, Intext or Reference) ###
### Return location + surrounding text. 
def findlocation():
    # Footnote

    # Citation

    # Reference
    pass
###

def extractURL(string):
    # Creating an empty list
    url_list = []
    true_url = []
      
    # Regular Expression to extract URL from the string
    regex = r'\b((?:https?|ftp|file):\/\/[-a-zA-Z0-9+&@#\/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#\/%=~_|])'
      
    # Compile the Regular Expression
    p = re.compile(regex, re.IGNORECASE)
      
    # Find the match between string and the regular expression
    m = p.finditer(string)
      
    # Find the next subsequence of the input subsequence that find the pattern
    for match in m:
        # Find the substring from the first index of match result to the last index of match result and add in the list
        url_list.append(match.group())
      
    # If no URL is present
    if len(url_list) == 0:
        print("-1")
        return
      
    # Print all the URLs stored
    for url in url_list:

        #check if found URL is a valid URL
        if is_string_an_url(url):
            true_url.append(url)

        else:
            print('wrong URL:', url)

    return true_url

def is_string_an_url(url_string: str) -> bool:
    result = validators.url(url_string)

    return result if result else False

def is_dataset_or_database(url, title):
    # Regular expressions to match common dataset/database keywords
    dataset_keywords = ["dataset", "data set", "data", "database", "db"]
    
    # Check if any dataset keyword is present in the title
    for keyword in dataset_keywords:
        if re.search(r'\b{}\b'.format(keyword), title, re.IGNORECASE):
            return True
    
    # Check if the URL contains dataset-specific terms
    url_keywords = ["data", "dataset", "db", "database"]
    if any(keyword in url for keyword in url_keywords):
        return True
    
    return False

    text_object.citation_analyze()
    def citation_analyze(self):
        # function returns all references that contain a URL and returns the reference soup and the surrounding reference paragraph.

        # find all references in the bibliography that contain a link
        ptr_children = self.soup.select('listBibl ptr')

        # find the entire reference 'surrounding' that link
        all_ref_containing_links = [child.parent.parent for child in ptr_children]

        # these are all the reference ids for the references that contain a URL
        ref_ids = [ref_containing_link['xml:id'] for ref_containing_link in all_ref_containing_links]
        
        # ref dict consisting of ref ID as a key and full reference from the citations as a value
        ref_dict = {}
        for ref_id, ref_containing_link in zip(ref_ids, all_ref_containing_links):
            ref_dict[ref_id] = ref_containing_link

        # loop over the references in the text to see if they are linked to any of the URL containing references. 
        # failed list provides us with the references that grobid did not link to anythin in the text
        failed_list = []
        URL_ref_dict = {}

        for up_ref in self.soup.find_all('ref', type="bibr"):
            try:
                target = up_ref['target'][1:]

            except:
                failed_list.append(up_ref)
                continue
            
            # if the target is in the ref dict, we have found an in-text reference that links to a reference that contains a URL
            if target in ref_dict.keys():
                down_ref = ref_dict[target]
 
                
                URL_ref_dict[down_ref] = up_ref



class Paper:
    def __init__(self, tei_doc):
        self.tei = tei_doc
        with open(tei_doc, 'r') as tei:
            self.soup = BeautifulSoup(tei, features="xml")
        self.title = self.soup.title.getText()
        self.doi = self.doi_retrieve()
        self.url = self.tika_check()
        self.paragraphs = self.paragrapher()
        self.references = self.reference_finder()
        self.citations = self.citation_finder()

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

        # loop over paragraphs
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
        self.candidate_datasets = []

    def intext_url(self):
        # checks for all the in_text URLs if they are a dataset according to the three heuristics.

        for i, all_url_in_paragraph in enumerate(self.paper.in_text_URL()):
            
            if all_url_in_paragraph != []:
                
                for url in all_url_in_paragraph:
                    context = self.paper.paragraphs[i].getText()
                    
                    # h1 not available
                    self.h2(url, context)
                    # h3 in development

    def footnote_url(self):
        # retrieves all the different footnotes and checks with the three heuristics whether they belong to a dataset or not

        for i, all_footnotes_in_paragraph in enumerate(self.paper.footnote_finder()):
            
            if all_footnotes_in_paragraph != []:

                for footnote in all_footnotes_in_paragraph:
                    
                    text = footnote.getText()
                    url = self.paper.extractURL(text)[0]
                    self.h2(url, text)

    def citation_url(self):
        # retrieves the citations and checks with the three developed hueristics whether the link points to a dataset or not.

        for i, citation_per_paragraph in enumerate(self.paper.reference_matcher()):
            
            paragraph = self.paper.paragraphs[i].getText()

            if citation_per_paragraph != []:

                for citation in citation_per_paragraph:
                    
                    try:
                        # find all citations containing links and extracting the citation context (text surrounding the link, which includes author name and title text).
                        url = citation.find('ptr')['target']
                        context = citation.find('ptr').parent
                        title = context.find('title').getText()
                        author_name = citation.find('persName').getText()
                        citation_context = title + ' ' + author_name + ' ' # + url

                    except:
                        continue

                    ### codeblock to implement context analysis
                    self.h2(url, citation_context)
                    ### codeblock to implement context analysis

                    ### codeblock to implement analysis of paragraph surrounding reference
                    self.h2(url, paragraph)
                    ### codeblock to implement analysis of paragraph surrounding reference

    def h1(self):
        # Citation context analysis
        pass

    def h2(self, url, context):
        keywords = ['dataset', 'database', 'data', 'repository', 'archive', 'corpus', 'catalog', 'benchmark', 'information']  # List of keywords to search for

        # Create a regular expression pattern using the keywords
        pattern = r'(?:{})'.format('|'.join(map(re.escape, keywords)))

        # Search for the pattern in the context string
        match = re.search(pattern, context, re.IGNORECASE)

        # if match:
        #     self.url_dict[url] = True  # Increment the value by one
        # else:
        #     self.url_dict[url] = True  # Decrement the value by one
       
        if match:
            self.url_dict[url] = self.url_dict.get(url, 0) + 1  # Increment the value by one
        else:
            self.url_dict[url] = self.url_dict.get(url, 0) - 1  # Decrement the value by one
        

    def h3(self):
        # URL metadata check

        pass

if __name__ == "__main__":
    tei_doc = '1-s2.0-S0308521X18307728-main.pdf.tei.xml'
    text_object = Paper(tei_doc)

    print(text_object.store_info_as_json('output.json'))

    
            