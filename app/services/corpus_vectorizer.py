import json
import re
from dataclasses import dataclass
from pathlib import Path
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


_TOKEN_PATTERN = re.compile(r"[A-Za-zA-ZА-Яа-яЁё0-9ʻʼ'`-]+", re.UNICODE)


@dataclass(frozen=True)
class CorpusDocument:
    doc_id: str
    source: str
    article_id: str
    title: str
    content: str

    @property
    def text(self) -> str:
        return " ".join(part for part in (self.title, self.content) if part).strip()

    @property
    def label(self) -> str:
        return self.source.replace("'", "")


class LexCorpusVectorizer:
    def __init__(self, corpus_dir: str = "lex_structured", max_docs: int | None = None) -> None:
        self._corpus_dir = self._resolve_corpus_dir(corpus_dir)
        docs = self._load_documents()
        if max_docs is not None:
            docs = docs[:max_docs]
        self.documents = docs
        self.texts = [doc.text for doc in self.documents]

    @staticmethod
    def _resolve_corpus_dir(corpus_dir: str) -> Path:
        candidate = Path(corpus_dir)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        cwd_candidate = Path.cwd() / candidate
        if cwd_candidate.exists():
            return cwd_candidate

        repo_root = Path(__file__).resolve().parents[2]
        repo_candidate = repo_root / candidate
        if repo_candidate.exists():
            return repo_candidate

        return repo_candidate

    def _load_documents(self) -> list[CorpusDocument]:
        documents: list[CorpusDocument] = []
        for path in sorted(self._corpus_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)

            source = path.stem
            for article_id, article in payload.items():
                content = self.normalize_text(article.get("content", ""))
                title = self.normalize_text(article.get("title", ""))
                if not content:
                    continue
                documents.append(
                    CorpusDocument(
                        doc_id=f"{source}:{article_id}",
                        source=source,
                        article_id=str(article_id),
                        title=title,
                        content=content,
                    )
                )
        return documents

    @staticmethod
    def normalize_text(text: str) -> str:
        tokens = _TOKEN_PATTERN.findall(text.lower())
        return " ".join(tokens)

    def build_bow(self, max_features: int | None = None):
        vectorizer = CountVectorizer(max_features=max_features)
        matrix = vectorizer.fit_transform(self.texts)
        return vectorizer, matrix

    def build_ngram(self, ngram_range: tuple[int, int] = (1, 2), max_features: int | None = None):
        vectorizer = CountVectorizer(ngram_range=ngram_range, max_features=max_features)
        matrix = vectorizer.fit_transform(self.texts)
        return vectorizer, matrix

    def build_tfidf(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int | None = None,
    ):
        vectorizer = TfidfVectorizer(ngram_range=ngram_range, max_features=max_features, min_df=0.2)
        matrix = vectorizer.fit_transform(self.texts)
        return vectorizer, matrix

    def get_bow_dataframe(self, max_features: int | None = None) -> pd.DataFrame:
        vectorizer, matrix = self.build_bow(max_features=max_features)
        index = [f"text_{i}" for i in range(len(self.texts))]
        return pd.DataFrame(matrix.toarray(), columns=vectorizer.get_feature_names_out(), index=index)

    def get_ngram_dataframe(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int | None = None,
    ) -> pd.DataFrame:
        vectorizer, matrix = self.build_ngram(ngram_range=ngram_range, max_features=max_features)
        index = [f"text_{i}" for i in range(len(self.texts))]
        return pd.DataFrame(matrix.toarray(), columns=vectorizer.get_feature_names_out(), index=index)

    def get_tfidf_dataframe(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int | None = None,
    ) -> pd.DataFrame:
        vectorizer, matrix = self.build_tfidf(ngram_range=ngram_range, max_features=max_features)
        index = [f"text_{i}" for i in range(len(self.texts))]
        return pd.DataFrame(matrix.toarray(), columns=vectorizer.get_feature_names_out(), index=index)

    def get_labels(self) -> list[str]:
        return [doc.label for doc in self.documents]

    def get_label_distribution(self) -> pd.DataFrame:
        counts = Counter(self.get_labels())
        return pd.DataFrame(
            [{"label": label, "document_count": count} for label, count in sorted(counts.items())]
        )

    def get_classification_dataset(self, min_samples_per_class: int = 2) -> tuple[list[str], list[str]]:
        labels = self.get_labels()
        counts = Counter(labels)

        filtered_texts: list[str] = []
        filtered_labels: list[str] = []
        for text, label in zip(self.texts, labels, strict=False):
            if counts[label] >= min_samples_per_class:
                filtered_texts.append(text)
                filtered_labels.append(label)

        return filtered_texts, filtered_labels

def main() -> None:
    service = LexCorpusVectorizer()
    print("\n=== BoW DataFrame ===")
    df_bow = service.get_bow_dataframe()
    print(df_bow)
    print(f"\n[{df_bow.shape[0]} rows x {df_bow.shape[1]} columns]")
    
    print("\n=== N-Gram DataFrame ===")
    df_ngram = service.get_ngram_dataframe()
    print(df_ngram)
    print(f"\n[{df_ngram.shape[0]} rows x {df_ngram.shape[1]} columns]")
    
    print("\n=== TF-IDF DataFrame ===")
    df_tfidf = service.get_tfidf_dataframe()
    print(df_tfidf)
    print(f"\n[{df_tfidf.shape[0]} rows x {df_tfidf.shape[1]} columns]")


if __name__ == "__main__":
    main()
