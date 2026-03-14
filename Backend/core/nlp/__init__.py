"""
NLP Module - Natural Language Processing Components.

This module provides NLP capabilities including BERT-based
Named Entity Recognition for resume extraction.
"""

from core.nlp.bert_ner import (
    BERTNERExtractor,
    create_ner_extractor
)

__all__ = [
    "BERTNERExtractor",
    "create_ner_extractor",
]
