from paper import Paper
from context_extract import contextExtractor

if __name__ == "__main__":

    tei_doc = '1-s2.0-S0308521X18307728-main.pdf.tei.xml'
    paper = Paper(tei_doc)

    context_extractor = contextExtractor(paper, candidate_dataset_names = ['CAPRI', 'FADN', 'Agricultural Outlook'])


    context_extractor.dataset()

    print(context_extractor.url_dict)
