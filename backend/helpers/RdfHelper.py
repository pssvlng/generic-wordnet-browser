from typing import Optional, List, Tuple
import requests
from rdflib import Graph, Literal, URIRef
from rdflib.plugins.sparql import prepareQuery
from models.RdfLiteral import RdfLiteral
from bs4 import BeautifulSoup

from models.RdfNonLiteral import RdfNonLiteral

class RdfHelper:

    @classmethod
    def get_rdf_graph(cls, url: str, accept_headers: List[str]) -> Optional[Graph]:        
        headers = {'Accept': ', '.join(accept_headers)}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            content_type = response.headers.get('content-type').split(';')[0]
            is_xml = content_type == 'text/xml'            
            if content_type in accept_headers or is_xml:
                rdf_data = response.text
                try:
                    if is_xml: 
                        content_type = 'xml'
                    graph = Graph().parse(data=rdf_data, format=content_type)
                    return graph
                except Exception as e:
                    raise requests.RequestException(f"Failed to parse RDF data: {e}")

        return None
    
    @classmethod    
    def get_attribute_in_rdf_graph(cls, graph: Graph, attribute: URIRef, lang: str = None) -> Optional[Literal]:        
        
        if lang:
            for _, predicate, obj in graph:
                if predicate == attribute and isinstance(obj, Literal) and obj.language == lang:
                    return obj
                
            for _, predicate, obj in graph:
                    if predicate == attribute:
                        return obj        
        return None
    
    @classmethod
    def get_literals_in_rdf_graph(cls, graph: Graph, lang: str = None) -> (List[RdfLiteral], str):
        rows = []
        return_lang = lang
        if lang:
            query = prepareQuery(
                        """
                        SELECT ?subject ?predicate ?literal
                        WHERE {
                            ?subject ?predicate ?literal .
                            FILTER (isLiteral(?literal) && langMatches(lang(?literal), "{return_lang}"))
                        }
                        """)
            rows = list(graph.query(query))
        
        if len(rows) == 0:            
            query = prepareQuery(
                        """
                        SELECT ?subject ?predicate ?literal
                        WHERE {
                            ?subject ?predicate ?literal .
                            FILTER (isLiteral(?literal) && langMatches(lang(?literal), "en"))
                        }
                        """)
            rows = list(graph.query(query))            

        if len(rows) == 0:
            query = prepareQuery(
                        """
                        SELECT ?subject ?predicate ?literal
                        WHERE {
                            ?subject ?predicate ?literal .
                            FILTER (isLiteral(?literal))
                        }
                        """)
            rows = list(graph.query(query))        
        else:
            return_lang = "en"    

        results = set()
        for row in rows:                
            soup = BeautifulSoup(str(row.literal), 'html.parser')
            results.add(RdfLiteral(str(row.predicate), soup.get_text()))    

        return (list(results), return_lang)

    @classmethod
    def get_non_literals_in_rdf_graph(cls, graph: Graph) -> List[RdfNonLiteral]:        
        query = prepareQuery(
                    """
                    SELECT ?subject ?predicate ?nonLiteral
                    WHERE {
                        ?subject ?predicate ?nonLiteral .
                        FILTER (!isLiteral(?nonLiteral))
                    }
                    """)
        results = set()
        for row in graph.query(query):
            if isinstance(row.nonLiteral, URIRef):                
                results.add(RdfNonLiteral(str(row.predicate), str(row.nonLiteral)))    

        return list(results)

            