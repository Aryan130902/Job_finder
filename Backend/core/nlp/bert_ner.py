"""
BERT-based Named Entity Recognition (NER) for Resume Extraction.

This module provides NLP capabilities for extracting structured information
from resume text using BERT models.
"""

import os
import re
import torch
from transformers import BertTokenizer, BertForTokenClassification, BertModel, BertTokenizerFast
from typing import Dict, List, Optional


class BERTNERExtractor:
    """
    Extracts named entities from resume text using BERT.
    
    Supports extraction of names, emails, phone numbers, education details,
    companies, designations, skills, and experience information.
    """
    
    LABEL_MAP = {
        "O": "Outside",
        "B-NAME": "Name",
        "I-NAME": "Name",
        "B-EMAIL": "Email",
        "I-EMAIL": "Email",
        "B-PHONE": "Phone",
        "I-PHONE": "Phone",
        "B-EDU": "Education",
        "I-EDU": "Education",
        "B-COLLEGE": "College",
        "I-COLLEGE": "College",
        "B-DEGREE": "Degree",
        "I-DEGREE": "Degree",
        "B-COMPANY": "Company",
        "I-COMPANY": "Company",
        "B-DESIGNATION": "Designation",
        "I-DESIGNATION": "Designation",
        "B-SKILL": "Skill",
        "I-SKILL": "Skill",
        "B-EXPERIENCE": "Experience",
        "I-EXPERIENCE": "Experience",
        "B-YEAR": "Year",
        "I-YEAR": "Year",
    }

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the BERT NER extractor.
        
        Args:
            model_path: Path to the BERT model. If None, uses default cache location.
        """
        self.model_path = model_path or os.path.expanduser(
            r"C:\Users\aryan\.cache\huggingface\hub\models--bert-base-uncased"
            r"\snapshots\86b5e0934494bd15c9632b12f734a8a67f723594"
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.tokenizer = BertTokenizerFast.from_pretrained(self.model_path)
        self.bert_model = BertModel.from_pretrained(self.model_path)
        self.bert_model.to(self.device)
        self.bert_model.eval()
        
        self.ner_head = None
        self._init_ner_head()
    
    def _init_ner_head(self):
        """Initialize the NER classification head."""
        num_labels = len(self.LABEL_MAP)
        self.ner_head = BertForTokenClassification.from_pretrained(
            self.model_path,
            num_labels=num_labels
        )
        self.ner_head.to(self.device)
        self.ner_head.eval()
    
    def _get_label_id(self, label: str) -> int:
        """Get label ID from label string."""
        return list(self.LABEL_MAP.keys()).index(label)
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """
        Extract entities using BERT NER model.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            List of extracted entities with type and text
        """
        words = text.split()
        encodings = self.tokenizer(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        input_ids = encodings["input_ids"].to(self.device)
        attention_mask = encodings["attention_mask"].to(self.device)
        
        with torch.no_grad():
            outputs = self.ner_head(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=2)
        
        predictions = predictions.cpu().numpy()[0]
        word_ids = encodings.word_ids()
        
        entities = []
        current_entity = None
        current_type = None
        current_text = ""
        
        for idx, (word_id, pred) in enumerate(zip(word_ids, predictions)):
            if word_id is None:
                continue
            
            if word_id != current_entity:
                if current_entity is not None and current_type:
                    entities.append({
                        "text": current_text,
                        "type": self.LABEL_MAP[current_type]
                    })
                current_entity = word_id
                current_text = words[word_id]
                current_type = self.LABEL_MAP.get(pred, "O")
                if current_type == "Outside":
                    current_type = None
            else:
                if current_type == self.LABEL_MAP.get(pred, "O"):
                    current_text += " " + words[word_id]
        
        if current_entity is not None and current_type:
            entities.append({
                "text": current_text,
                "type": current_type
            })
        
        return entities
    
    def extract_entities_rule_based(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using rule-based patterns.
        
        Uses regex patterns to extract common resume fields like
        emails, phone numbers, education, skills, etc.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            Dictionary mapping entity types to list of extracted values
        """
        entities = {
            "name": [],
            "email": [],
            "phone": [],
            "education": [],
            "college": [],
            "degree": [],
            "company": [],
            "designation": [],
            "skills": [],
            "experience": [],
            "years": []
        }
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|(?:\+?91[-.\s]?)?[0-9]{10}'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        
        entities["email"] = list(set(emails))
        entities["phone"] = list(set(phones))
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            
            if any(word in line_lower for word in ['b.tech', 'm.tech', 'b.e', 'm.e', 'b.sc', 'm.sc', 'ph.d', 'phd', 'bca', 'mca', 'mba', 'degree', 'diploma']):
                if 'university' in line_lower or 'college' in line_lower or 'institute' in line_lower:
                    entities["college"].append(line.strip())
                entities["education"].append(line.strip())
                entities["degree"].append(line.strip())
            
            if any(word in line_lower for word in ['university', 'college', 'institute', 'school']):
                if line.strip() not in entities["college"]:
                    entities["college"].append(line.strip())
            
            if any(word in line_lower for word in ['junior', 'senior', 'intern', 'trainee', 'associate', 'engineer', 'developer', 'manager', 'analyst', 'consultant', 'lead', 'head']):
                entities["designation"].append(line.strip())
        
        skill_keywords = [
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express',
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'jira',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
            'nlp', 'computer vision', 'data science', 'data analysis', 'sql', 'tableau',
            'html', 'css', 'bootstrap', 'typescript', 'rest api', 'graphql', 'microservices',
            'linux', 'unix', 'bash', 'powershell', 'agile', 'scrum', 'rest', 'api'
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title() if len(skill) > 3 else skill.upper())
        entities["skills"] = list(set(found_skills))
        
        experience_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience',
            r'experience\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)',
            r'(?:worked|working)\s*(?:as|at)\s*(?:a|an)?\s*([^.]+?)(?:\s+for|\s+since)',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["experience"].extend(matches)
        
        year_pattern = r'(?:20[1-2][0-9]|19[9][0-9])'
        years = re.findall(year_pattern, text)
        entities["years"] = list(set(years))
        
        return entities
    
    def extract_from_text(self, text: str) -> Dict:
        """
        Extract all entities from text using rule-based extraction.
        
        Args:
            text: Input resume text
            
        Returns:
            Dictionary of extracted entities
        """
        entities = self.extract_entities_rule_based(text)
        
        first_line = text.split('\n')[0].strip()
        if first_line:
            email_check = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            phone_check = re.compile(r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}')
            if not email_check.match(first_line) and not phone_check.match(first_line):
                if len(first_line.split()) <= 4:
                    if not entities["name"]:
                        entities["name"] = [first_line]
        
        return entities
    
    def extract_from_file(self, file_path: str) -> Dict:
        """
        Extract entities from a file.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary of extracted entities
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return self.extract_from_text(text)


def create_ner_extractor() -> BERTNERExtractor:
    """
    Factory function to create a BERT NER extractor.
    
    Returns:
        Initialized BERTNERExtractor instance
    """
    return BERTNERExtractor()
