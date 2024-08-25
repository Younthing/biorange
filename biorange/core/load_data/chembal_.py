"""
This module provides functionality for interacting with the UniProt and ChEMBL APIs 
predict targets from SMILES strings and enhance these predictionswith gene names for Homo sapiens.
Constants:
    POLLING_INTERVAL: The interval (in seconds) to wait between polling attempts.
    API_URL: The base URL for the UniProt API.
    retries: A Retry object that defines the retry strategy for requests.
    session: A requests.Session object with the retry strategy applied.
"""

import re
import time
import json
import zlib
from xml.etree import ElementTree
from urllib.parse import urlparse, parse_qs, urlencode
import logging
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd


logger = logging.getLogger("biotree.smiles_to_target.chembal")

# Official API
POLLING_INTERVAL = 3
API_URL = "https://rest.uniprot.org"

retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retries))


def check_response(response):
    """Check the response status and raise an HTTPError if the response contains an error.

    Args:
        response (requests.Response): The response object to check.

    Raises:
        requests.HTTPError: If the response status code is an error.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(response.json())
        raise


def submit_id_mapping(from_db, to_db, ids):
    """Submit a job for ID mapping from one database to another.

    Args:
        from_db (str): The source database.
        to_db (str): The target database.
        ids (list of str): The list of IDs to map.

    Returns:
        str: The job ID for the submitted ID mapping job.
    """
    request = requests.post(
        f"{API_URL}/idmapping/run",
        data={"from": from_db, "to": to_db, "ids": ",".join(ids)},
        timeout=600,
    )
    check_response(request)
    return request.json()["jobId"]


def get_next_link(headers):
    """Extract the next link from the response headers.

    Args:
        headers (dict): The response headers.

    Returns:
        str: The next link URL if it exists, otherwise None.
    """
    re_next_link = re.compile(r'<(.+)>; rel="next"')
    if "Link" in headers:
        match = re_next_link.match(headers["Link"])
        if match:
            return match.group(1)


def check_id_mapping_results_ready(job_id):
    """Check if the ID mapping results are ready.

    Args:
        job_id (str): The job ID to check.

    Returns:
        bool: True if the results are ready, False otherwise.

    Raises:
        Exception: If the job status is not RUNNING or completed.
    """
    while True:
        request = session.get(f"{API_URL}/idmapping/status/{job_id}")
        check_response(request)
        j = request.json()
        if "jobStatus" in j:
            if j["jobStatus"] == "RUNNING":
                print(f"Retrying in {POLLING_INTERVAL}s")
                time.sleep(POLLING_INTERVAL)
            else:
                raise Exception(j["jobStatus"])
        else:
            return bool(j["results"] or j["failedIds"])


def get_batch(batch_response, file_format, compressed):
    """Retrieve a batch of results from the response.

    Args:
        batch_response (requests.Response): The initial batch response.
        file_format (str): The file format of the results.
        compressed (bool): Whether the results are compressed.

    Yields:
        dict: The decoded batch results.
    """
    batch_url = get_next_link(batch_response.headers)
    while batch_url:
        batch_response = session.get(batch_url)
        batch_response.raise_for_status()
        yield decode_results(batch_response, file_format, compressed)
        batch_url = get_next_link(batch_response.headers)


def combine_batches(all_results, batch_results, file_format):
    """Combine batch results into a single result set.

    Args:
        all_results (dict): The combined results so far.
        batch_results (dict): The current batch of results.
        file_format (str): The file format of the results.

    Returns:
        dict: The combined results.
    """
    if file_format == "json":
        for key in ("results", "failedIds"):
            if key in batch_results and batch_results[key]:
                all_results[key] += batch_results[key]
    elif file_format == "tsv":
        return all_results + batch_results[1:]
    else:
        return all_results + batch_results
    return all_results


def get_id_mapping_results_link(job_id):
    """Retrieve the results link for the given job ID.

    Args:
        job_id (str): The job ID to get the results link for.

    Returns:
        str: The results link URL.
    """
    url = f"{API_URL}/idmapping/details/{job_id}"
    request = session.get(url)
    check_response(request)
    return request.json()["redirectURL"]


def decode_results(response, file_format, compressed):
    """Decode the results from the response.

    Args:
        response (requests.Response): The response object.
        file_format (str): The file format of the results.
        compressed (bool): Whether the results are compressed.

    Returns:
        dict or list: The decoded results.
    """
    if compressed:
        decompressed = zlib.decompress(response.content, 16 + zlib.MAX_WBITS)
        if file_format == "json":
            j = json.loads(decompressed.decode("utf-8"))
            return j
        elif file_format == "tsv":
            return [line for line in decompressed.decode("utf-8").split("\n") if line]
        elif file_format == "xlsx":
            return [decompressed]
        elif file_format == "xml":
            return [decompressed.decode("utf-8")]
        else:
            return decompressed.decode("utf-8")
    elif file_format == "json":
        return response.json()
    elif file_format == "tsv":
        return [line for line in response.text.split("\n") if line]
    elif file_format == "xlsx":
        return [response.content]
    elif file_format == "xml":
        return [response.text]
    return response.text


def get_xml_namespace(element):
    """Get the XML namespace from an element.

    Args:
        element (xml.etree.ElementTree.Element): The XML element.

    Returns:
        str: The namespace URI.
    """
    m = re.match(r"\{(.*)\}", element.tag)
    return m.groups()[0] if m else ""


def merge_xml_results(xml_results):
    """Merge multiple XML results into a single XML document.

    Args:
        xml_results (list of str): The list of XML result strings.

    Returns:
        str: The merged XML document as a string.
    """
    merged_root = ElementTree.fromstring(xml_results[0])
    for result in xml_results[1:]:
        root = ElementTree.fromstring(result)
        for child in root.findall("{http://uniprot.org/uniprot}entry"):
            merged_root.insert(-1, child)
    ElementTree.register_namespace("", get_xml_namespace(merged_root[0]))
    return ElementTree.tostring(merged_root, encoding="utf-8", xml_declaration=True)


def print_progress_batches(batch_index, size, total):
    """Print the progress of fetching batches.

    Args:
        batch_index (int): The current batch index.
        size (int): The size of each batch.
        total (int): The total number of results.
    """
    n_fetched = min((batch_index + 1) * size, total)
    print(f"Fetched: {n_fetched} / {total}")


def get_id_mapping_results_search(url):
    """Retrieve ID mapping results using search.

    Args:
        url (str): The URL to retrieve the results from.

    Returns:
        dict or str: The results in the specified format.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    file_format = query["format"][0] if "format" in query else "json"
    if "size" in query:
        size = int(query["size"][0])
    else:
        size = 500
        query["size"] = size
    compressed = (
        query["compressed"][0].lower() == "true" if "compressed" in query else False
    )
    parsed = parsed._replace(query=urlencode(query, doseq=True))
    url = parsed.geturl()
    request = session.get(url)
    check_response(request)
    results = decode_results(request, file_format, compressed)
    total = int(request.headers["x-total-results"])
    print_progress_batches(0, size, total)
    for i, batch in enumerate(get_batch(request, file_format, compressed), 1):
        results = combine_batches(results, batch, file_format)
        print_progress_batches(i, size, total)
    if file_format == "xml":
        return merge_xml_results(results)
    return results


def get_id_mapping_results_stream(url):
    """Retrieve ID mapping results using streaming.

    Args:
        url (str): The URL to retrieve the results from.

    Returns:
        dict or list: The results in the specified format.
    """
    if "/stream/" not in url:
        url = url.replace("/results/", "/results/stream/")
    request = session.get(url)
    check_response(request)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    file_format = query["format"][0] if "format" in query else "json"
    compressed = (
        query["compressed"][0].lower() == "true" if "compressed" in query else False
    )
    return decode_results(request, file_format, compressed)


def convert_results_to_dataframe(results):
    """Convert the results to a pandas DataFrame.

    Args:
        results (dict): The results to convert.

    Returns:
        pandas.DataFrame: The results as a DataFrame.
    """
    rows = []
    for result in results["results"]:
        from_value = result["from"]
        primary_accession = result["to"]["primaryAccession"]
        genes = result["to"]["genes"]
        genes_value = genes[0]["geneName"]["value"] if genes else None
        organism = result["to"]["organism"]["scientificName"]

        rows.append([from_value, primary_accession, genes_value, organism])

    df = pd.DataFrame(
        rows, columns=["chembal", "uniport_accession", "gene_name", "organism"]
    )

    return df


def get_dataframe_from_ids(ids):
    """Retrieve a DataFrame from a list of IDs.

    Args:
        ids (list of str): The list of IDs to retrieve data for.

    Returns:
        pandas.DataFrame: The data as a DataFrame.
    """
    job_id = submit_id_mapping(from_db="ChEMBL", to_db="UniProtKB", ids=ids)
    if check_id_mapping_results_ready(job_id):
        link = get_id_mapping_results_link(job_id)
        results_dict = get_id_mapping_results_search(link)
        return convert_results_to_dataframe(results_dict)


def get_target_predictions(smiles):
    """Retrieve target predictions for a given SMILES string.

    Args:
        smiles (str): The SMILES string to get predictions for.

    Returns:
        pandas.DataFrame: The target predictions.
    """
    url = "https://www.ebi.ac.uk/chembl/target-predictions"
    headers = {"Content-Type": "application/json"}
    payload = {"smiles": smiles}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=600)
        response.raise_for_status()

        data = response.json()
        result_df = pd.DataFrame(data)
        result_df.insert(0, "smiles", smiles)
        return result_df
    except requests.exceptions.RequestException as e:
        logger.error("Request failed for %s with error: %s", smiles, e)
        return None


def add_gene_name_to_predictions(smiles):
    """Add gene names to the target predictions for a given SMILES string.

    Args:
        smiles (str): The SMILES string to get predictions for.

    Returns:
        pandas.DataFrame: The target predictions with gene names.
    """
    df_predictions = get_target_predictions(smiles)
    df_filtered = df_predictions[
        (df_predictions["organism"] == "Homo sapiens")
        & (df_predictions["80%"] == "active")
    ]
    unique_chembl_ids = df_filtered["target_chemblid"].unique().tolist()

    df_genes = get_dataframe_from_ids(unique_chembl_ids)
    df_genes = df_genes[["chembal", "gene_name"]]

    df_merged = pd.merge(
        df_filtered,
        df_genes,
        left_on="target_chemblid",
        right_on="chembal",
        how="left",
    )

    df_merged = df_merged.drop(columns=["chembal"])

    return df_merged


# if __name__ == "__main__":
#     # Example usage
#     smiles = "CC(C)C1=CC=C(C=C1)C(C)C(=O)O"
#     result_df = add_gene_name_to_predictions(smiles)
#     print(result_df)
