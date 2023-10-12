"""Query a corpus and get results."""
import json
import logging
import requests


def query(customer_id: int, corpus_id: int, api_key: str, query: str):
    """This method queries the data.
    Args:
        customer_id: Unique customer ID in vectara platform.
        corpus_id: ID of the corpus to which data needs to be indexed.
        query_address: Address of the querying server. e.g., api.vectara.io
        api_key: API key of the customer.
        query: Query to be run.
    Returns:
        (response, True) in case of success and returns (error, False) in case
         of failure.

    """
    post_headers = {"x-api-key": f"{api_key}", "customer-id": f"{customer_id}"}

    response = requests.post("https://api.vectara.io/v1/query",
                             data=_get_query_json(customer_id, corpus_id,
                                                  query),
                             verify=True,
                             timeout=30,
                             headers=post_headers)

    if response.status_code != 200:
        logging.error("Query failed with code %d, reason %s, text %s",
                      response.status_code, response.reason, response.text)
        return response, False
    return response, True


def _get_query_json(customer_id, corpus_id, query_value):
    query = {}
    query_obj = {}

    query_obj["query"] = query_value
    query_obj["num_results"] = 5

    corpus_key = {}
    corpus_key["customer_id"] = customer_id
    corpus_key["corpus_id"] = corpus_id
    corpus_key["lexical_interpolation_config"] = {"lambda": 0.002}
    query_obj["corpus_key"] = [corpus_key]

    context_config = {
        "sentences_before": 2,
        "sentences_after": 2,
    }

    query["contex_config"] = [context_config]

    summarization_request = {
        "summarizer_prompt_name": "vectara-summary-ext-v1.2.0",
        "response_lang": "en",
        "max_summarized_results": 5
    }
    query_obj["summary"] = [summarization_request]

    query["query"] = [query_obj]

    return json.dumps(query)
