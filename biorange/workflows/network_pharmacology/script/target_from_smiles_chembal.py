import json
import re
import time
import zlib
from typing import Any, Dict, Generator, List, Optional, Union
from urllib.parse import parse_qs, urlencode, urlparse
from xml.etree import ElementTree

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

from biorange.core.logger import get_logger

logger = get_logger(__name__)

# Constants
POLLING_INTERVAL = 3
API_URL = "https://rest.uniprot.org"

# Retry strategy for requests
retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retries))


class ChEMBLTargetScraper:
    def __init__(self):
        self.session = session

    def check_response(self, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"HTTPError: {e.response.json()}")
            raise

    def submit_id_mapping(self, from_db: str, to_db: str, ids: List[str]) -> str:
        response = self.session.post(
            f"{API_URL}/idmapping/run",
            data={"from": from_db, "to": to_db, "ids": ",".join(ids)},
            timeout=600,
        )
        self.check_response(response)
        return response.json()["jobId"]

    def get_next_link(self, headers: Dict[str, str]) -> Optional[str]:
        if "Link" in headers:
            match = re.match(r'<(.+)>; rel="next"', headers["Link"])
            return match.group(1) if match else None
        return None

    def check_id_mapping_results_ready(self, job_id: str) -> bool:
        while True:
            response = self.session.get(f"{API_URL}/idmapping/status/{job_id}")
            self.check_response(response)
            status = response.json().get("jobStatus")
            if status == "RUNNING":
                logger.info(f"Retrying in {POLLING_INTERVAL}s")
                time.sleep(POLLING_INTERVAL)
            elif status:
                raise Exception(status)
            else:
                return bool(
                    response.json().get("results") or response.json().get("failedIds")
                )

    def get_batch(
        self, batch_url: str, file_format: str, compressed: bool
    ) -> Generator[Union[Dict[str, Any], List[str]], None, None]:
        while batch_url:
            response = self.session.get(batch_url)
            self.check_response(response)
            yield self.decode_results(response, file_format, compressed)
            batch_url = self.get_next_link(response.headers)

    def combine_batches(
        self,
        all_results: Union[Dict[str, Any], List[str]],
        batch_results: Union[Dict[str, Any], List[str]],
        file_format: str,
    ) -> Union[Dict[str, Any], List[str]]:
        if file_format == "json":
            for key in ("results", "failedIds"):
                if key in batch_results:
                    all_results[key].extend(batch_results[key])
        elif file_format in {"tsv", "xml"}:
            all_results.extend(
                batch_results[1:] if file_format == "tsv" else batch_results
            )
        else:
            all_results += batch_results
        return all_results

    def get_id_mapping_results_link(self, job_id: str) -> str:
        response = self.session.get(f"{API_URL}/idmapping/details/{job_id}")
        self.check_response(response)
        return response.json()["redirectURL"]

    def decode_results(
        self, response: requests.Response, file_format: str, compressed: bool
    ) -> Union[Dict[str, Any], List[str], str]:
        content = (
            zlib.decompress(response.content, 16 + zlib.MAX_WBITS)
            if compressed
            else response.content
        )
        if file_format == "json":
            return json.loads(content.decode("utf-8"))
        elif file_format == "tsv":
            return content.decode("utf-8").splitlines()
        elif file_format in {"xlsx", "xml"}:
            return [content]
        return content.decode("utf-8")

    def get_xml_namespace(self, element: ElementTree.Element) -> str:
        match = re.match(r"\{(.*)\}", element.tag)
        return match.group(1) if match else ""

    def merge_xml_results(self, xml_results: List[str]) -> str:
        merged_root = ElementTree.fromstring(xml_results[0])
        namespace = self.get_xml_namespace(merged_root[0])
        for result in xml_results[1:]:
            root = ElementTree.fromstring(result)
            for child in root.findall(f"{{{namespace}}}entry"):
                merged_root.append(child)
        ElementTree.register_namespace("", namespace)
        return ElementTree.tostring(merged_root, encoding="utf-8", xml_declaration=True)

    def print_progress_batches(self, batch_index: int, size: int, total: int) -> None:
        n_fetched = min((batch_index + 1) * size, total)
        logger.info(f"Fetched: {n_fetched} / {total}")

    def get_id_mapping_results_search(self, url: str) -> Union[Dict[str, Any], str]:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        file_format = query.get("format", ["json"])[0]
        size = int(query.get("size", [500])[0])
        compressed = query.get("compressed", ["false"])[0].lower() == "true"
        parsed = parsed._replace(query=urlencode(query, doseq=True))
        url = parsed.geturl()

        response = self.session.get(url)
        self.check_response(response)
        results = self.decode_results(response, file_format, compressed)
        total = int(response.headers["x-total-results"])
        self.print_progress_batches(0, size, total)

        for i, batch in enumerate(
            self.get_batch(
                self.get_next_link(response.headers), file_format, compressed
            ),
            1,
        ):
            results = self.combine_batches(results, batch, file_format)
            self.print_progress_batches(i, size, total)

        return self.merge_xml_results(results) if file_format == "xml" else results

    def get_id_mapping_results_stream(
        self, url: str
    ) -> Union[Dict[str, Any], List[str]]:
        if "/stream/" not in url:
            url = url.replace("/results/", "/results/stream/")
        response = self.session.get(url)
        self.check_response(response)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        file_format = query.get("format", ["json"])[0]
        compressed = query.get("compressed", ["false"])[0].lower() == "true"
        return self.decode_results(response, file_format, compressed)

    def convert_results_to_dataframe(self, results: Dict[str, Any]) -> pd.DataFrame:
        rows = [
            [
                result["from"],
                result["to"]["primaryAccession"],
                (
                    result["to"]["genes"][0]["geneName"]["value"]
                    if result["to"]["genes"]
                    else None
                ),
                result["to"]["organism"]["scientificName"],
            ]
            for result in results["results"]
        ]
        return pd.DataFrame(
            rows, columns=["chembal", "uniport_accession", "gene_name", "organism"]
        )

    def get_dataframe_from_ids(self, ids: List[str]) -> pd.DataFrame:
        job_id = self.submit_id_mapping(from_db="ChEMBL", to_db="UniProtKB", ids=ids)
        if self.check_id_mapping_results_ready(job_id):
            link = self.get_id_mapping_results_link(job_id)
            results_dict = self.get_id_mapping_results_search(link)
            return self.convert_results_to_dataframe(results_dict)
        return pd.DataFrame()

    def get_target_predictions(self, smiles: str) -> pd.DataFrame:
        """
        从ChEMBL获取目标预测。

        Args:
            smiles (str): 化合物的SMILES表示。

        Returns:
            pd.DataFrame: 包含目标预测结果的DataFrame。如果请求失败，返回空DataFrame。

        Raises:
            requests.exceptions.RequestException: 如果API请求失败。
        """
        url = "https://www.ebi.ac.uk/chembl/target-predictions"
        headers = {"Content-Type": "application/json"}
        payload = {"smiles": smiles}
        try:
            response = self.session.post(
                url, headers=headers, json=payload, timeout=600
            )
            self.check_response(response)
            data = response.json()
            result_df = pd.DataFrame(data)
            result_df.insert(0, "smiles", smiles)
            return result_df
        except requests.exceptions.RequestException as e:
            logger.error(f"Returning empty DataFrame for {smiles} with error: {e}")
            return pd.DataFrame()

    def search_smiles(self, smiles: str) -> pd.DataFrame:
        df_predictions = self.get_target_predictions(smiles)
        if df_predictions.empty:
            return pd.DataFrame()

        df_filtered = df_predictions[
            (df_predictions["organism"] == "Homo sapiens")
            & (df_predictions["80%"] == "active")
        ]
        unique_chembl_ids = df_filtered["target_chemblid"].unique().tolist()

        df_genes = self.get_dataframe_from_ids(unique_chembl_ids)
        df_genes = df_genes[["chembal", "gene_name"]]

        df_merged = pd.merge(
            df_filtered,
            df_genes,
            left_on="target_chemblid",
            right_on="chembal",
            how="left",
        )
        df_merged.drop(columns=["chembal"], inplace=True)
        # 增加一列source
        df_merged["source"] = "chembal"

        return df_merged


if __name__ == "__main__":
    client = ChEMBLTargetScraper()
    smiles = "CCO"
    df = client.search_smiles(smiles)
    df.to_csv("output.csv", index=False)
