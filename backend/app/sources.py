from datetime import date

import httpx

from .retrieval import Document


class SourceError(RuntimeError):
    pass


class PubMedClient:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search(self, query: str, limit: int = 10) -> list[Document]:
        try:
            response = httpx.get(
                f"{self.base_url}/esearch.fcgi",
                params={"db": "pubmed", "term": query, "retmode": "json", "retmax": limit},
                timeout=20,
            )
            response.raise_for_status()
            ids = response.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            details = httpx.get(
                f"{self.base_url}/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                timeout=20,
            )
            details.raise_for_status()
            result = details.json().get("result", {})
            return [
                Document(
                    document_id=f"pubmed:{identifier}",
                    title=result.get(identifier, {}).get("title", "Untitled PubMed record"),
                    text=self._text(result.get(identifier, {})),
                    source="pubmed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{identifier}/",
                    publication_date=result.get(identifier, {}).get("pubdate"),
                )
                for identifier in ids
            ]
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise SourceError(f"PubMed request failed: {exc}") from exc

    @staticmethod
    def _text(item: dict) -> str:
        return f"{item.get('title', '')}. Journal: {item.get('fulljournalname', '')}."


class ClinicalTrialsClient:
    base_url = "https://clinicaltrials.gov/api/v2/studies"

    def search(self, query: str, limit: int = 10) -> list[Document]:
        try:
            response = httpx.get(
                self.base_url,
                params={"query.term": query, "pageSize": limit, "format": "json"},
                timeout=20,
            )
            response.raise_for_status()
            studies = response.json().get("studies", [])
            documents = []
            for study in studies:
                protocol = study.get("protocolSection", {})
                identification = protocol.get("identificationModule", {})
                status = protocol.get("statusModule", {})
                identifier = identification.get("nctId")
                if not identifier:
                    continue
                title = identification.get("briefTitle", "Untitled clinical trial")
                documents.append(Document(
                    document_id=f"clinicaltrials:{identifier}",
                    title=title,
                    text=f"{title}. Overall status: {status.get('overallStatus', 'unknown')}.",
                    source="clinicaltrials.gov",
                    url=f"https://clinicaltrials.gov/study/{identifier}",
                    publication_date=date.today().isoformat(),
                ))
            return documents
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise SourceError(f"ClinicalTrials.gov request failed: {exc}") from exc
