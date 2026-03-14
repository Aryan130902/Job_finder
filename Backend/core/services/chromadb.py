"""
ChromaDB Service for Resume Vector Storage and Search.

This module provides vector embedding storage and semantic search
capabilities for resumes using ChromaDB.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime


class ChromaDBService:
    """
    Service for managing resume embeddings in ChromaDB.
    
    Provides methods for adding, searching, updating, and deleting
    resume embeddings with metadata.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the ChromaDB service.
        
        Args:
            persist_directory: Directory to persist the ChromaDB database
        """
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.resume_collection = self.client.get_or_create_collection(
            name="resumes",
            metadata={"description": "Resume embeddings for candidate search"}
        )
        self.skills_collection = self.client.get_or_create_collection(
            name="skills",
            metadata={"description": "Skills embeddings for matching"}
        )
        self.experience_collection = self.client.get_or_create_collection(
            name="experience",
            metadata={"description": "Experience embeddings"}
        )
    
    def _generate_embedding(self, text: str, bert_model, bert_tokenizer, device) -> List[float]:
        """
        Generate BERT embedding for text.
        
        Args:
            text: Text to generate embedding for
            bert_model: BERT model instance
            bert_tokenizer: BERT tokenizer instance
            device: torch device
            
        Returns:
            List of float values representing the embedding
        """
        import torch
        inputs = bert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = bert_model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        return embedding.tolist()
    
    def add_resume(
        self,
        resume_data: Dict[str, Any],
        bert_model,
        bert_tokenizer,
        device
    ) -> str:
        """
        Add a resume to the vector database.
        
        Args:
            resume_data: Dictionary containing resume information
            bert_model: BERT model for embedding generation
            bert_tokenizer: BERT tokenizer
            device: torch device
            
        Returns:
            Generated resume ID
        """
        resume_id = str(uuid.uuid4())
        
        combined_text = self._create_combined_text(resume_data)
        embedding = self._generate_embedding(combined_text, bert_model, bert_tokenizer, device)
        
        metadata = {
            "name": resume_data.get("name", ""),
            "email": resume_data.get("email", ""),
            "phone": resume_data.get("phone", ""),
            "skills": ",".join(resume_data.get("skills", [])),
            "company": ",".join(resume_data.get("company_name", [])),
            "college": ",".join(resume_data.get("college_name", [])),
            "designation": ",".join(resume_data.get("designation", [])),
            "experience": ",".join(resume_data.get("experience", [])),
            "total_experience": resume_data.get("total_experience", ""),
            "education": ",".join(resume_data.get("education", [])),
            "created_at": datetime.now().isoformat(),
            "resume_text": combined_text[:1000]
        }
        
        self.resume_collection.add(
            ids=[resume_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        
        self._add_skills(resume_id, resume_data, bert_model, bert_tokenizer, device)
        self._add_experience(resume_id, resume_data, bert_model, bert_tokenizer, device)
        
        return resume_id
    
    def _create_combined_text(self, resume_data: Dict) -> str:
        """Create combined text representation of resume for embedding."""
        parts = []
        
        if resume_data.get("name"):
            parts.append(f"Name: {resume_data['name']}")
        if resume_data.get("email"):
            parts.append(f"Email: {resume_data['email']}")
        if resume_data.get("phone"):
            parts.append(f"Phone: {resume_data['phone']}")
        if resume_data.get("skills"):
            parts.append(f"Skills: {', '.join(resume_data['skills'])}")
        if resume_data.get("education"):
            parts.append(f"Education: {', '.join(resume_data['education'])}")
        if resume_data.get("college_name"):
            parts.append(f"College: {', '.join(resume_data['college_name'])}")
        if resume_data.get("company_name"):
            parts.append(f"Companies: {', '.join(resume_data['company_name'])}")
        if resume_data.get("designation"):
            parts.append(f"Designations: {', '.join(resume_data['designation'])}")
        if resume_data.get("experience"):
            parts.append(f"Experience: {', '.join(resume_data['experience'])}")
        if resume_data.get("total_experience"):
            parts.append(f"Total Experience: {resume_data['total_experience']}")
        
        return " | ".join(parts)
    
    def _add_skills(
        self,
        resume_id: str,
        resume_data: Dict,
        bert_model,
        bert_tokenizer,
        device
    ):
        """Add skill embeddings to the skills collection."""
        skills = resume_data.get("skills", [])
        
        for i, skill in enumerate(skills):
            skill_id = f"{resume_id}_skill_{i}"
            embedding = self._generate_embedding(skill, bert_model, bert_tokenizer, device)
            
            self.skills_collection.add(
                ids=[skill_id],
                embeddings=[embedding],
                metadatas=[{
                    "resume_id": resume_id,
                    "skill": skill,
                    "type": "skill"
                }]
            )
    
    def _add_experience(
        self,
        resume_id: str,
        resume_data: Dict,
        bert_model,
        bert_tokenizer,
        device
    ):
        """Add experience embeddings to the experience collection."""
        companies = resume_data.get("company_name", [])
        designations = resume_data.get("designation", [])
        
        for i in range(min(len(companies), len(designations))):
            exp_id = f"{resume_id}_exp_{i}"
            exp_text = f"{designations[i]} at {companies[i]}"
            embedding = self._generate_embedding(exp_text, bert_model, bert_tokenizer, device)
            
            self.experience_collection.add(
                ids=[exp_id],
                embeddings=[embedding],
                metadatas=[{
                    "resume_id": resume_id,
                    "company": companies[i],
                    "designation": designations[i],
                    "type": "experience"
                }]
            )
    
    def search_by_skill(
        self,
        skill_query: str,
        bert_model,
        bert_tokenizer,
        device,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search resumes by skill.
        
        Args:
            skill_query: Skill to search for
            bert_model: BERT model
            bert_tokenizer: BERT tokenizer
            device: torch device
            top_k: Number of results to return
            
        Returns:
            List of matching resumes with metadata
        """
        query_embedding = self._generate_embedding(skill_query, bert_model, bert_tokenizer, device)
        
        results = self.skills_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return self._format_search_results(results)
    
    def search_by_text(
        self,
        query_text: str,
        bert_model,
        bert_tokenizer,
        device,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search resumes by text query.
        
        Args:
            query_text: Text query
            bert_model: BERT model
            bert_tokenizer: BERT tokenizer
            device: torch device
            top_k: Number of results to return
            
        Returns:
            List of matching resumes with metadata
        """
        query_embedding = self._generate_embedding(query_text, bert_model, bert_tokenizer, device)
        
        results = self.resume_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return self._format_search_results(results)
    
    def search_by_experience(
        self,
        experience_query: str,
        bert_model,
        bert_tokenizer,
        device,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search resumes by experience.
        
        Args:
            experience_query: Experience query
            bert_model: BERT model
            bert_tokenizer: BERT tokenizer
            device: torch device
            top_k: Number of results to return
            
        Returns:
            List of matching resumes with metadata
        """
        query_embedding = self._generate_embedding(experience_query, bert_model, bert_tokenizer, device)
        
        results = self.experience_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return self._format_search_results(results)
    
    def _format_search_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB query results into a list of dictionaries."""
        formatted = []
        
        if not results or not results.get("ids"):
            return formatted
        
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None,
                "metadata": results["metadatas"][0][i] if "metadatas" in results else {}
            })
        
        return formatted
    
    def get_resume_by_id(self, resume_id: str) -> Optional[Dict]:
        """
        Get a specific resume by ID.
        
        Args:
            resume_id: Resume ID to retrieve
            
        Returns:
            Resume data or None if not found
        """
        results = self.resume_collection.get(ids=[resume_id])
        
        if not results or not results.get("ids"):
            return None
        
        return {
            "id": results["ids"][0],
            "metadata": results["metadatas"][0] if results.get("metadatas") else {},
            "embedding": results["embeddings"][0] if results.get("embeddings") else []
        }
    
    def get_all_resumes(self) -> List[Dict]:
        """
        Get all resumes from the database.
        
        Returns:
            List of all resumes with metadata
        """
        results = self.resume_collection.get()
        
        if not results or not results.get("ids"):
            return []
        
        resumes = []
        for i in range(len(results["ids"])):
            resumes.append({
                "id": results["ids"][i],
                "metadata": results["metadatas"][i] if results.get("metadatas") else {}
            })
        
        return resumes
    
    def delete_resume(self, resume_id: str) -> bool:
        """
        Delete a resume and its associated embeddings.
        
        Args:
            resume_id: ID of the resume to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.resume_collection.delete(ids=[resume_id])
            self.skills_collection.delete(where={"resume_id": resume_id})
            self.experience_collection.delete(where={"resume_id": resume_id})
            return True
        except Exception:
            return False
    
    def update_resume(
        self,
        resume_id: str,
        resume_data: Dict,
        bert_model,
        bert_tokenizer,
        device
    ) -> bool:
        """
        Update a resume in the database.
        
        Args:
            resume_id: ID of the resume to update
            resume_data: New resume data
            bert_model: BERT model
            bert_tokenizer: BERT tokenizer
            device: torch device
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.delete_resume(resume_id)
            self.add_resume(resume_data, bert_model, bert_tokenizer, device)
            return True
        except Exception:
            return False
    
    def count_resumes(self) -> int:
        """
        Get the total number of resumes in the database.
        
        Returns:
            Count of resumes
        """
        return self.resume_collection.count()


_chroma_service = None


def get_chroma_service(persist_directory: str = "./chroma_db") -> ChromaDBService:
    """
    Get or create a singleton ChromaDB service instance.
    
    Args:
        persist_directory: Directory for database persistence
        
    Returns:
        ChromaDBService instance
    """
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaDBService(persist_directory)
    return _chroma_service
