from fuzzywuzzy import fuzz

class contextExtractor:
    # takes as input a paper object and outputs a classification of the URLs present. 

    def __init__(self, paper_object, candidate_dataset_names):
        self.paper = paper_object
        self.url_dict = {}
        self.candidate_dataset_names = candidate_dataset_names

    def dataset(self):
        # iterates over the candidate datasets to find a suitable URL

        for dataset in self.candidate_dataset_names:
            
            self.reference_iterator(dataset)

    def reference_iterator(self, dataset):

        for reference in self.paper.citations:
            
            try:
                reference_id = reference.find('ptr').parent.parent['xml:id']
                url = reference.find('ptr')['target']
                context = reference.find('ptr').parent
                title = context.find('title').getText()

            except:
                continue

            if reference.find('persName'):
                author_name = reference.find('persName').getText()
                if self.h2(dataset,author_name):
                    self.url_dict[dataset] = url 

            if reference.find('orgName'):
                org_name = reference.find('orgName').getText()

                if self.h2(dataset,org_name):
                    self.url_dict[dataset] = url


            if self.h2(dataset, title):

                self.url_dict[dataset] = url  
            


    def find_mentions(self, dataset):
        # finds all mentions of a given dataset

        for (paragraph, reference_list, footnote_list) in zip(self.paper.paragraphs, self.paper.references, self.paper.footnote_finder()):
            paragraph_text = paragraph.getText()
            
            # if there is a reference in the current paragraph:
            # if reference_list:
            #     self.reference_analysis(dataset, paragraph, reference_list)

            # self.footnote_analysis(dataset, paragraph, footnote_list)

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
        # This heuristic checks whether dataset_name has a large string similarity with string. It also generates potential acronyms from string and dataset_name.

        # generate possible acronyms of length of the dataset name 
        potential_words = self.get_acron(string, len([*dataset_name]))

        # add the original string that is to be checked to the possible acronyms it generated
        potential_words.append(string)

        # also add the individual words to the list of potential dataset names.
        if len(string.split()) > 2:
            [potential_words.append(i) for i in string.split()]

        # first loop loops over the dataset_name that was given but also generate its acronym 
        for potential in [dataset_name, ''.join([word[0] for word in dataset_name.split()])]:

            for possible_match in potential_words:

                similarity_score = fuzz.ratio(potential.lower(), possible_match.lower())

                if similarity_score >= threshold:
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